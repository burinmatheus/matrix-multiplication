# Makefile - Multiplicação de Matrizes GIGANTES
# MPI + OpenMP com Otimizações Avançadas

# Compiladores
MPICC = mpicc
CC = gcc

# Diretórios
SRC_DIR = src
BIN_DIR = bin
OBJ_DIR = obj

# Flags de compilação otimizadas
CFLAGS = -O3 -Wall -fopenmp -march=native -mtune=native -I$(SRC_DIR) -std=c99
LDFLAGS = -fopenmp -lm

# Executável de multiplicação GIGANTE
EXEC = $(BIN_DIR)/matrix_giant
SRC = $(SRC_DIR)/matrix_mult_giant.c

# Alvos
.PHONY: all clean test bench plot help dirs

all: dirs $(EXEC)

# Criar diretórios
dirs:
	@mkdir -p $(BIN_DIR) $(OBJ_DIR)

# Compilar
$(EXEC): $(SRC) | dirs
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║  Compilando Multiplicação de Matrizes GIGANTES (Otimizado)    ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@$(MPICC) $(CFLAGS) $(SRC) -o $(EXEC) $(LDFLAGS)
	@echo "✓ Executável criado: $(EXEC)"
	@echo ""

# Limpeza
clean:
	@echo "Limpando arquivos..."
	@rm -rf $(OBJ_DIR) $(BIN_DIR)
	@rm -f matrix_giant_metrics.csv matrix_giant_analysis.png
	@echo "✓ Limpeza concluída"

# Teste rápido
test: $(EXEC)
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║              TESTE RÁPIDO - Matrizes GIGANTES                 ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "1. Matriz 1000×1000 com 2 processos × 2 threads:"
	@mpirun -np 2 $(EXEC) -n 1000 -t 2
	@echo ""
	@echo "2. Matriz 1500×1500 com 4 processos × 4 threads:"
	@mpirun -np 4 $(EXEC) -n 1500 -t 4
	@echo ""

# Benchmark automático (executa no devcontainer boot)
bench: $(EXEC)
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║          BENCHMARK AUTOMÁTICO - Matrizes GIGANTES             ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@bash scripts/auto_benchmark.sh

# Alias para bench
auto: bench

# Gerar apenas gráficos (requer benchmark prévio)
plot:
	@echo "Gerando gráficos de análise..."
	@python3 scripts/plot_giant.py

# Exemplos de execução
examples: $(EXEC)
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║                   EXEMPLOS DE USO                             ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Exemplo 1: Matriz 2000×2000 (4 processos, 4 threads cada)"
	@mpirun -np 4 $(EXEC) -n 2000 -t 4
	@echo ""
	@echo "Exemplo 2: Matriz 3000×3000 (8 processos, 4 threads cada)"
	@mpirun -np 8 $(EXEC) -n 3000 -t 4
	@echo ""

# Teste de escalabilidade
scale: $(EXEC)
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║             TESTE DE ESCALABILIDADE                           ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "=== Matriz 2000×2000 com diferentes configurações ==="
	@echo ""
	@echo "▶ 1 processo × 4 threads:"
	@mpirun -np 1 $(EXEC) -n 2000 -t 4 | grep -E "(Tempo|GFLOPS)"
	@echo ""
	@echo "▶ 2 processos × 4 threads:"
	@mpirun -np 2 $(EXEC) -n 2000 -t 4 | grep -E "(Tempo|GFLOPS)"
	@echo ""
	@echo "▶ 4 processos × 4 threads:"
	@mpirun -np 4 $(EXEC) -n 2000 -t 4 | grep -E "(Tempo|GFLOPS)"
	@echo ""
	@echo "▶ 8 processos × 2 threads:"
	@mpirun -np 8 $(EXEC) -n 2000 -t 2 | grep -E "(Tempo|GFLOPS)"
	@echo ""

# Ajuda
help:
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║    MULTIPLICAÇÃO DE MATRIZES GIGANTES - MPI + OpenMP          ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Alvos disponíveis:"
	@echo "  make                - Compila o executável (padrão)"
	@echo "  make clean          - Remove arquivos compilados"
	@echo "  make test           - Teste rápido"
	@echo "  make bench          - Benchmark automático (800 e 1500)"
	@echo "  make auto           - Alias para bench"
	@echo "  make plot           - Gera gráficos do último benchmark"
	@echo "  make examples       - Executa exemplos práticos"
	@echo "  make scale          - Teste de escalabilidade"
	@echo "  make help           - Mostra esta ajuda"
	@echo ""
	@echo "Uso do programa:"
	@echo "  mpirun -np <P> ./$(EXEC) -n <N> -t <T> [opções]"
	@echo ""
	@echo "Argumentos:"
	@echo "  -n <tamanho>    Tamanho da matriz NxN (padrão: 2000)"
	@echo "  -t <threads>    Threads OpenMP por processo (padrão: 4)"
	@echo "  --seq           Executar versão sequencial (comparação)"
	@echo "  --verify        Verificar resultado (amostragem)"
	@echo ""
	@echo "Exemplos:"
	@echo "  mpirun -np 4 ./$(EXEC) -n 2000 -t 4"
	@echo "  mpirun -np 8 ./$(EXEC) -n 3000 -t 8"
	@echo "  mpirun -np 4 ./$(EXEC) -n 5000 -t 4"
	@echo ""
	@echo "📚 Documentação completa: cat README.md"
	@echo ""
