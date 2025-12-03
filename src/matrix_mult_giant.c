#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <mpi.h>
#include <omp.h>
#include <time.h>
#include <string.h>

#define MASTER 0
#define TILE_SIZE 64  // Otimizado para cache L1/L2

// Usar malloc simples - o alinhamento não é crítico para correção
#define aligned_alloc(alignment, size) malloc(size)

// Estrutura para armazenar métricas
typedef struct {
    double sequential_time;
    double parallel_time;
    double speedup;
    double efficiency;
    double gflops;
    int num_processes;
    int num_threads;
    int matrix_size;
} Metrics;

// Função para inicializar matriz
void initialize_matrix(double *matrix, int rows, int cols, int seed) {
    srand(seed + omp_get_thread_num());
    #pragma omp parallel for
    for (int i = 0; i < rows * cols; i++) {
        matrix[i] = (double)(rand() % 100) / 10.0;
    }
}

// Multiplicação sequencial otimizada com transposta e tiling
double sequential_multiplication_optimized(double *A, double *B, double *C, int n) {
    double start_time = omp_get_wtime();
    
    // Transpor B para melhor localidade de cache
    double *B_T = (double *)aligned_alloc(64, n * n * sizeof(double));
    
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            B_T[j * n + i] = B[i * n + j];
        }
    }
    
    // Multiplicação com tiling e B transposta
    for (int ii = 0; ii < n; ii += TILE_SIZE) {
        for (int jj = 0; jj < n; jj += TILE_SIZE) {
            for (int i = ii; i < (ii + TILE_SIZE < n ? ii + TILE_SIZE : n); i++) {
                for (int j = jj; j < (jj + TILE_SIZE < n ? jj + TILE_SIZE : n); j++) {
                    double sum = 0.0;
                    for (int k = 0; k < n; k++) {
                        sum += A[i * n + k] * B_T[j * n + k];
                    }
                    C[i * n + j] = sum;
                }
            }
        }
    }
    
    free(B_T);
    double end_time = omp_get_wtime();
    return end_time - start_time;
}

// Multiplicação paralela híbrida OTIMIZADA
double parallel_multiplication_optimized(double *A, double *B, double *C, int n, int rank, int size) {
    double start_time = MPI_Wtime();
    
    // Calcular distribuição de linhas
    int rows_per_process = n / size;
    int remainder = n % size;
    int local_rows = rows_per_process + (rank < remainder ? 1 : 0);
    
    // Preparar scatter/gather
    int *sendcounts = NULL;
    int *displs = NULL;
    
    if (rank == MASTER) {
        sendcounts = (int *)malloc(size * sizeof(int));
        displs = (int *)malloc(size * sizeof(int));
        
        int offset = 0;
        for (int i = 0; i < size; i++) {
            int rows = rows_per_process + (i < remainder ? 1 : 0);
            sendcounts[i] = rows * n;
            displs[i] = offset;
            offset += sendcounts[i];
        }
    }
    
    // Alocar buffers locais alinhados para melhor performance
    double *local_A = (double *)aligned_alloc(64, local_rows * n * sizeof(double));
    
    // Distribuir A
    MPI_Scatterv(A, sendcounts, displs, MPI_DOUBLE,
                 local_A, local_rows * n, MPI_DOUBLE,
                 MASTER, MPI_COMM_WORLD);
    
    // Broadcast B (todos precisam de B completo)
    MPI_Bcast(B, n * n, MPI_DOUBLE, MASTER, MPI_COMM_WORLD);
    
    // Transpor B em paralelo com OpenMP
    double *B_T = (double *)aligned_alloc(64, n * n * sizeof(double));
    
    #pragma omp parallel for collapse(2) schedule(static)
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            B_T[j * n + i] = B[i * n + j];
        }
    }
    
    // Buffer para resultado local
    double *local_C = (double *)aligned_alloc(64, local_rows * n * sizeof(double));
    
    // Multiplicação local híbrida otimizada
    // Usar schedule(guided) para melhor balanceamento em matrizes gigantes
    // guided: divide as iterações do loop de forma dinâmica
    #pragma omp parallel for schedule(guided, 8)
    for (int i = 0; i < local_rows; i++) {
        for (int j = 0; j < n; j++) {
            double sum = 0.0;
            
            // Instrui o compilador a tentar paralelizar as iterações do loop usando instruções SIMD.
            // SIMD permite que múltiplos dados sejam processados em uma única operação.
            // Sem reduction, várias threads tentariam somar em sum ao mesmo tempo → race condition!
            #pragma omp simd reduction(+:sum)
            for (int k = 0; k < n; k++) {
                sum += local_A[i * n + k] * B_T[j * n + k];
            }
            
            local_C[i * n + j] = sum;
        }
    }
    
    // Reunir resultados
    MPI_Gatherv(local_C, local_rows * n, MPI_DOUBLE,
                C, sendcounts, displs, MPI_DOUBLE,
                MASTER, MPI_COMM_WORLD);
    
    double end_time = MPI_Wtime();
    
    // Limpeza
    free(local_A);
    free(local_C);
    free(B_T);
    if (rank == MASTER) {
        free(sendcounts);
        free(displs);
    }
    
    return end_time - start_time;
}

// Verificação rápida (amostragem para matrizes gigantes)
int verify_result_sampled(double *C1, double *C2, int n, double tolerance, int sample_rate) {
    int samples = 0;
    int errors = 0;
    
    for (int i = 0; i < n; i += sample_rate) {
        for (int j = 0; j < n; j += sample_rate) {
            samples++;
            if (fabs(C1[i * n + j] - C2[i * n + j]) > tolerance) {
                errors++;
                if (errors <= 5) {  // Mostrar apenas primeiros erros
                    printf("Erro em [%d,%d]: %.6f vs %.6f (diff: %.6e)\n", 
                           i, j, C1[i * n + j], C2[i * n + j], 
                           fabs(C1[i * n + j] - C2[i * n + j]));
                }
            }
        }
    }
    
    if (errors > 0) {
        printf("Total de erros: %d de %d amostras (%.2f%%)\n", 
               errors, samples, (100.0 * errors) / samples);
    }
    
    return errors == 0;
}

// Função para carregar tempo sequencial baseline
double load_sequential_baseline(int n) {
    FILE *file = fopen("matrix_giant_baseline.txt", "r");
    if (!file) return -1.0;
    
    int size;
    double seq_time;
    while (fscanf(file, "%d,%lf\n", &size, &seq_time) == 2) {
        if (size == n) {
            fclose(file);
            return seq_time;
        }
    }
    fclose(file);
    return -1.0;
}

// Função para salvar tempo sequencial baseline
void save_sequential_baseline(int n, double seq_time) {
    FILE *file = fopen("matrix_giant_baseline.txt", "a");
    if (file) {
        fprintf(file, "%d,%.6f\n", n, seq_time);
        fclose(file);
    }
}

// Salvar métricas
void save_metrics(Metrics *metrics, const char *filename) {
    FILE *file = fopen(filename, "a");
    if (file == NULL) return;
    
    fseek(file, 0, SEEK_END);
    if (ftell(file) == 0) {
        fprintf(file, "MatrixSize,NumProcesses,NumThreads,SeqTime(s),ParTime(s),Speedup,Efficiency(%%),GFLOPS\n");
    }
    
    fprintf(file, "%d,%d,%d,%.6f,%.6f,%.4f,%.2f,%.2f\n",
            metrics->matrix_size,
            metrics->num_processes,
            metrics->num_threads,
            metrics->sequential_time,
            metrics->parallel_time,
            metrics->speedup,
            metrics->efficiency,
            metrics->gflops);
    
    fclose(file);
}

// Imprimir métricas
void print_metrics(Metrics *metrics) {
    printf("\n");
    printf("╔═════════════════════════════════════════════════════════════╗\n");
    printf("║              MÉTRICAS DE DESEMPENHO - GIGANTE               ║\n");
    printf("╚═════════════════════════════════════════════════════════════╝\n");
    printf("Tamanho da matriz      : %d x %d (%.1f milhões de elementos)\n", 
           metrics->matrix_size, metrics->matrix_size, 
           (metrics->matrix_size * metrics->matrix_size) / 1e6);
    printf("Processos MPI          : %d\n", metrics->num_processes);
    printf("Threads OpenMP/processo: %d\n", metrics->num_threads);
    printf("Cores totais           : %d\n", metrics->num_processes * metrics->num_threads);
    printf("─────────────────────────────────────────────────────────────\n");
    if (metrics->sequential_time > 0) {
        printf("Tempo sequencial       : %.4f segundos\n", metrics->sequential_time);
    }
    printf("Tempo paralelo         : %.4f segundos\n", metrics->parallel_time);
    if (metrics->speedup > 0) {
        printf("Speedup                : %.4fx\n", metrics->speedup);
        printf("Eficiência             : %.2f%%\n", metrics->efficiency);
    }
    printf("Performance            : %.2f GFLOPS\n", metrics->gflops);
    printf("═════════════════════════════════════════════════════════════\n\n");
}

int main(int argc, char *argv[]) {
    int rank, size;
    int n = 2000;  // Tamanho padrão das matrizes (grande)
    int run_sequential = 0;  // Desabilitado por padrão para grandes matrizes
    int num_threads = 4;  // Número de threads por processo
    int verify = 0;  // Flag para verificação de resultado (pode ser cara para grandes matrizes)
    
    // Inicializa o ambiente MPI
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);  // Obtém o rank do processo atual
    MPI_Comm_size(MPI_COMM_WORLD, &size);  // Obtém o número total de processos
    
    // Processamento de argumentos passados via linha de comando
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-n") == 0 && i + 1 < argc) {
            n = atoi(argv[i + 1]);  // Define o tamanho da matriz
            i++;
        } else if (strcmp(argv[i], "-t") == 0 && i + 1 < argc) {
            num_threads = atoi(argv[i + 1]);  // Define o número de threads
            i++;
        } else if (strcmp(argv[i], "--seq") == 0) {
            run_sequential = 1;  // Habilita execução sequencial
        } else if (strcmp(argv[i], "--verify") == 0) {
            verify = 1;  // Habilita verificação de resultados
        }
    }
    
    omp_set_num_threads(num_threads);  // Define o número de threads para OpenMP
    
    // Impressão de informações gerais (apenas para o processo mestre)
    if (rank == MASTER) {
        printf("\n");
        printf("╔═════════════════════════════════════════════════════════════╗\n");
        printf("║    MULTIPLICAÇÃO DE MATRIZES GIGANTES - MPI + OpenMP        ║\n");
        printf("╚═════════════════════════════════════════════════════════════╝\n");
        printf("Tamanho da matriz      : %d x %d\n", n, n);
        printf("Elementos totais       : %.2f milhões\n", (n * n) / 1e6);
        printf("Memória por matriz     : %.2f MB\n", (n * n * sizeof(double)) / (1024.0 * 1024.0));
        printf("Memória total (3 matr.): %.2f MB\n", (3.0 * n * n * sizeof(double)) / (1024.0 * 1024.0));
        printf("Processos MPI          : %d\n", size);
        printf("Threads OpenMP/processo: %d\n", num_threads);
        printf("Cores totais           : %d\n", size * num_threads);
        printf("Verificação            : %s\n", verify ? "SIM (amostragem)" : "NÃO");
        printf("═════════════════════════════════════════════════════════════\n\n");
    }
    
    // Alocação das matrizes A, B, C_seq e C_par
    double *A = NULL, *B = NULL, *C_seq = NULL, *C_par = NULL;
    
    if (rank == MASTER) {
        // Aloca as matrizes A, B e C_par para o processo mestre
        printf("Alocando matrizes...\n");
        A = (double *)aligned_alloc(64, n * n * sizeof(double));
        B = (double *)aligned_alloc(64, n * n * sizeof(double));
        C_par = (double *)aligned_alloc(64, n * n * sizeof(double));
        
        // Inicializa as matrizes A e B
        printf("Inicializando matrizes A e B...\n");
        initialize_matrix(A, n, n, 42);  // Preenche A com valores
        initialize_matrix(B, n, n, 123); // Preenche B com valores
        printf("✓ Matrizes inicializadas\n\n");
    } else {
        // Os outros processos alocam apenas as matrizes B e C_par
        B = (double *)aligned_alloc(64, n * n * sizeof(double));
        C_par = (double *)aligned_alloc(64, n * n * sizeof(double));
    }
    
    // Estrutura para armazenar métricas de desempenho
    Metrics metrics;
    metrics.matrix_size = n;
    metrics.num_processes = size;
    metrics.num_threads = num_threads;
    
    // Carrega o tempo base da execução sequencial, se existir
    double baseline_time = -1.0;
    if (rank == MASTER) {
        baseline_time = load_sequential_baseline(n);
    }
    
    // Execução sequencial (apenas para o mestre)
    if (rank == MASTER && (run_sequential || baseline_time < 0.0)) {
        // Aloca a matriz C_seq se necessário
        if (!C_seq) {
            C_seq = (double *)aligned_alloc(64, n * n * sizeof(double));
        }
        
        // Executa a multiplicação sequencial otimizada
        printf("Executando multiplicação SEQUENCIAL otimizada...");
        if (baseline_time < 0.0) {
            printf(" (gerando baseline)\n");
        } else {
            printf("\n");
        }
        fflush(stdout);
        metrics.sequential_time = sequential_multiplication_optimized(A, B, C_seq, n);  // Função de multiplicação sequencial
        printf("✓ Tempo sequencial: %.4f segundos\n\n", metrics.sequential_time);
        
        // Salva o tempo base, caso seja a primeira execução
        if (baseline_time < 0.0) {
            save_sequential_baseline(n, metrics.sequential_time);
            baseline_time = metrics.sequential_time;
        }
    } else if (rank == MASTER && baseline_time >= 0.0) {
        // Usa o tempo base se ele já existir
        metrics.sequential_time = baseline_time;
        printf("Usando baseline sequencial: %.4f segundos\n\n", baseline_time);
    } else {
        metrics.sequential_time = 0.0;
    }
    
    // Sincroniza os processos
    MPI_Barrier(MPI_COMM_WORLD);
    
    // Execução paralela híbrida (MPI + OpenMP)
    if (rank == MASTER) {
        printf("Executando multiplicação PARALELA híbrida (MPI + OpenMP)...\n");
        fflush(stdout);
    }
    
    // Chama a função para execução paralela
    double parallel_time = parallel_multiplication_optimized(A, B, C_par, n, rank, size);
    
    if (rank == MASTER) {
        metrics.parallel_time = parallel_time;
        printf("✓ Tempo paralelo: %.4f segundos\n", metrics.parallel_time);
        
        // Calcula a quantidade de operações (GFLOPS)
        double flops = 2.0 * n * n * n;
        metrics.gflops = flops / (metrics.parallel_time * 1e9);
        
        // Verifica o resultado (se solicitado)
        if (verify && run_sequential) {
            printf("\nVerificando resultado (amostragem)...\n");
            int sample_rate = (n > 1000) ? 100 : 10;  // Taxa de amostragem para verificação
            if (verify_result_sampled(C_seq, C_par, n, 1e-6, sample_rate)) {
                printf("✓ Resultados corretos!\n");
            } else {
                printf("✗ Diferenças encontradas!\n");
            }
        }
        
        // Calcula métricas de desempenho (speedup e eficiência)
        if (metrics.sequential_time > 0.0) {
            metrics.speedup = metrics.sequential_time / metrics.parallel_time;
            metrics.efficiency = (metrics.speedup / (size * num_threads)) * 100.0;
        } else {
            metrics.speedup = 0.0;
            metrics.efficiency = 0.0;
        }
        
        // Exibe e salva as métricas
        print_metrics(&metrics);
        save_metrics(&metrics, "matrix_giant_metrics.csv");
        
        // Libera a memória das matrizes
        free(A);
        if (C_seq) free(C_seq);
    }
    
    // Libera a memória das matrizes B e C_par
    free(B);
    free(C_par);
    
    // Finaliza o ambiente MPI
    MPI_Finalize();
    return 0;
}