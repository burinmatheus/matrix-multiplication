#!/bin/bash

###############################################################################
# AUTO BENCHMARK - Executado automaticamente ao subir o devcontainer
# Testa diferentes configurações de MPI e OpenMP para identificar pontos ótimos
###############################################################################

set -e

# Detectar número de cores disponíveis
MAX_CORES=$(nproc)

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   BENCHMARK AUTOMÁTICO - Análise de Escalabilidade            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🖥️  Sistema detectado: $MAX_CORES cores disponíveis"
echo ""
echo "📊 Este benchmark testará:"
echo "   • Matriz GRANDE: 1500×1500 (3.4GB operações)"
echo "   • Matriz MÉDIA: 800×800 (1.0GB operações)"
echo "   • Variações: 1, 2, 4 processos MPI"
echo "   • Variações: 1, 2, 4, 8 threads OpenMP"
echo ""
echo "🎯 Objetivo: Identificar o ponto de quebra onde mais"
echo "   paralelismo não compensa para cada tamanho de matriz"
echo ""

# Limpar resultados anteriores
rm -f matrix_giant_metrics.csv matrix_giant_baseline.txt

# Contadores
TOTAL_TESTS=0
COMPLETED=0

# Configurações a testar
SIZES=(1500 800)
PROCESSES=(1 2 4)
THREADS=(1 2 4 8)

# Contar total de testes
for size in "${SIZES[@]}"; do
    for procs in "${PROCESSES[@]}"; do
        for threads in "${THREADS[@]}"; do
            total_cores=$((procs * threads))
            
            # Limitar ao número de cores disponíveis
            if [ $total_cores -le $MAX_CORES ]; then
                TOTAL_TESTS=$((TOTAL_TESTS + 1))
            fi
        done
    done
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Iniciando $TOTAL_TESTS testes..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Executar testes
for size in "${SIZES[@]}"; do
    echo "╔═══════════════════════════════════════════════════════════════╗"
    if [ $size -eq 1500 ]; then
        echo "║  MATRIZ GRANDE: ${size}×${size} (2.3 milhões elementos)             ║"
    else
        echo "║  MATRIZ MÉDIA: ${size}×${size} (640 mil elementos)                    ║"
    fi
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    
    for procs in "${PROCESSES[@]}"; do
        for threads in "${THREADS[@]}"; do
            total_cores=$((procs * threads))
            
            # Limitar ao número de cores disponíveis
            if [ $total_cores -le $MAX_CORES ]; then
                COMPLETED=$((COMPLETED + 1))
                echo -n "[$COMPLETED/$TOTAL_TESTS] ${size}×${size} | ${procs}P×${threads}T (${total_cores} cores) ... "
                
                # Executar teste (silencioso, apenas captura métricas)
                if mpirun --allow-run-as-root -np $procs ./bin/matrix_giant -n $size -t $threads > /dev/null 2>&1; then
                    echo "✓"
                else
                    echo "✗ (erro)"
                fi
            fi
        done
    done
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Benchmark concluído: $COMPLETED testes executados"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Gerar gráficos
echo "📊 Gerando análise gráfica..."
if python3 scripts/plot_giant.py; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  ✅ BENCHMARK AUTOMÁTICO CONCLUÍDO COM SUCESSO                ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 Resultados salvos em:"
    echo "   • matrix_giant_metrics.csv (dados brutos)"
    echo "   • matrix_giant_analysis.png (gráficos)"
    echo ""
    echo "🔍 Use 'make plot' para regenerar os gráficos"
    echo "🔍 Use 'make bench' para executar benchmark completo"
    echo ""
else
    echo "⚠️  Erro ao gerar gráficos"
fi
