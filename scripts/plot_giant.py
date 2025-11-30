#!/usr/bin/env python3
"""
Script para visualizar métricas de desempenho da multiplicação de matrizes gigantes
Gera gráficos detalhados de speedup, eficiência e GFLOPS
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def plot_giant_speedup(csv_file='matrix_giant_metrics.csv'):
    """Gera gráficos de análise completa de performance"""
    
    # Verificar se o arquivo existe
    if not os.path.exists(csv_file):
        print(f"❌ Erro: Arquivo {csv_file} não encontrado!")
        print("Execute o benchmark primeiro: make bench")
        return
    
    # Ler dados
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Erro ao ler arquivo CSV: {e}")
        return
    
    if df.empty:
        print("❌ Nenhum dado encontrado no arquivo CSV!")
        return
    
    print(f"✓ Carregados {len(df)} resultados de benchmark")
    
    # Calcular total de cores
    df['TotalCores'] = df['NumProcesses'] * df['NumThreads']
    
    # Criar figura com múltiplos subplots (4x3 = 12 gráficos)
    fig = plt.figure(figsize=(24, 16))
    fig.suptitle('Análise de Performance - Multiplicação de Matrizes GIGANTES (MPI + OpenMP)', 
                 fontsize=18, fontweight='bold')
    
    # 1. GFLOPS vs Total de Cores (por tamanho)
    ax1 = plt.subplot(4, 3, 1)
    for size in sorted(df['MatrixSize'].unique()):
        data = df[df['MatrixSize'] == size].sort_values('TotalCores')
        if len(data) > 0:
            ax1.plot(data['TotalCores'], data['GFLOPS'], 
                    marker='o', linewidth=2, markersize=8,
                    label=f'{size}×{size}')
    
    ax1.set_xlabel('Total de Cores (Processos × Threads)', fontsize=10)
    ax1.set_ylabel('GFLOPS', fontsize=10)
    ax1.set_title('1. Performance vs Cores', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log', base=2)
    
    # 2. Speedup vs Total de Cores (NOVA MÉTRICA)
    ax2 = plt.subplot(4, 3, 2)
    for size in sorted(df['MatrixSize'].unique()):
        data = df[df['MatrixSize'] == size].sort_values('TotalCores')
        if len(data) > 0:
            ax2.plot(data['TotalCores'], data['Speedup'], 
                    marker='s', linewidth=2, markersize=8,
                    label=f'{size}×{size}')
    
    # Linha de speedup ideal (linear)
    max_cores = df['TotalCores'].max()
    ideal_cores = np.arange(1, max_cores + 1)
    ax2.plot(ideal_cores, ideal_cores, 'k--', linewidth=2, alpha=0.5, label='Ideal (Linear)')
    
    ax2.set_xlabel('Total de Cores', fontsize=10)
    ax2.set_ylabel('Speedup', fontsize=10)
    ax2.set_title('2. Speedup vs Cores', fontsize=11, fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log', base=2)
    ax2.set_yscale('log', base=2)
    
    # 3. Efficiency vs Total de Cores (NOVA MÉTRICA)
    ax3 = plt.subplot(4, 3, 3)
    for size in sorted(df['MatrixSize'].unique()):
        data = df[df['MatrixSize'] == size].sort_values('TotalCores')
        if len(data) > 0:
            ax3.plot(data['TotalCores'], data['Efficiency(%)'], 
                    marker='D', linewidth=2, markersize=8,
                    label=f'{size}×{size}')
    
    # Linha de 100% efficiency
    ax3.axhline(y=100, color='green', linestyle='--', linewidth=2, alpha=0.5, label='100% Ideal')
    
    ax3.set_xlabel('Total de Cores', fontsize=10)
    ax3.set_ylabel('Eficiência (%)', fontsize=10)
    ax3.set_title('3. Eficiência vs Cores', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    ax3.set_xscale('log', base=2)
    
    # 4. Tempo Paralelo vs Sequencial
    ax4 = plt.subplot(4, 3, 4)
    for size in sorted(df['MatrixSize'].unique()):
        data = df[df['MatrixSize'] == size].sort_values('TotalCores')
        if len(data) > 0 and data.iloc[0]['SeqTime(s)'] > 0:
            seq_time = data.iloc[0]['SeqTime(s)']
            ax4.plot(data['TotalCores'], [seq_time] * len(data), 
                    linestyle='--', linewidth=2, alpha=0.5,
                    label=f'{size}×{size} (seq)')
            ax4.plot(data['TotalCores'], data['ParTime(s)'], 
                    marker='o', linewidth=2, markersize=8,
                    label=f'{size}×{size} (par)')
    
    ax4.set_xlabel('Total de Cores', fontsize=10)
    ax4.set_ylabel('Tempo (segundos)', fontsize=10)
    ax4.set_title('4. Tempo Paralelo vs Sequencial', fontsize=11, fontweight='bold')
    ax4.legend(fontsize=7)
    ax4.grid(True, alpha=0.3)
    ax4.set_xscale('log', base=2)
    ax4.set_yscale('log')
    
    # 5. GFLOPS por Processos MPI (fixando threads)
    ax5 = plt.subplot(4, 3, 5)
    for size in sorted(df['MatrixSize'].unique()):
        common_threads = df['NumThreads'].mode()[0]
        data = df[(df['MatrixSize'] == size) & (df['NumThreads'] == common_threads)]
        data = data.groupby('NumProcesses')['GFLOPS'].mean()
        if len(data) > 0:
            ax5.plot(data.index, data.values, 
                    marker='o', linewidth=2, markersize=8,
                    label=f'{size}×{size}')
    
    ax5.set_xlabel('Processos MPI', fontsize=10)
    ax5.set_ylabel('GFLOPS', fontsize=10)
    ax5.set_title(f'5. GFLOPS por Processos ({common_threads}T)', fontsize=11, fontweight='bold')
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3)
    
    # 6. GFLOPS por Threads OpenMP (fixando processos)
    ax6 = plt.subplot(4, 3, 6)
    for size in sorted(df['MatrixSize'].unique()):
        common_procs = df['NumProcesses'].mode()[0]
        data = df[(df['MatrixSize'] == size) & (df['NumProcesses'] == common_procs)]
        data = data.groupby('NumThreads')['GFLOPS'].mean()
        if len(data) > 0:
            ax6.plot(data.index, data.values, 
                    marker='s', linewidth=2, markersize=8,
                    label=f'{size}×{size}')
    
    ax6.set_xlabel('Threads OpenMP', fontsize=10)
    ax6.set_ylabel('GFLOPS', fontsize=10)
    ax6.set_title(f'6. GFLOPS por Threads ({common_procs}P)', fontsize=11, fontweight='bold')
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.3)
    
    # 7. Heatmap de GFLOPS (Processos vs Threads)
    ax7 = plt.subplot(4, 3, 7)
    
    # 7. Heatmap de GFLOPS (Processos vs Threads)
    ax7 = plt.subplot(4, 3, 7)
    
    # Usar o tamanho mais comum ou o maior
    sizes = sorted(df['MatrixSize'].unique())
    main_size = sizes[-1] if len(sizes) > 0 else df['MatrixSize'].mode()[0]
    
    pivot_data = df[df['MatrixSize'] == main_size].groupby(['NumProcesses', 'NumThreads'])['GFLOPS'].mean().reset_index()
    pivot_table = pivot_data.pivot(index='NumThreads', columns='NumProcesses', values='GFLOPS')
    
    if not pivot_table.empty:
        im = ax7.imshow(pivot_table, cmap='YlOrRd', aspect='auto')
        ax7.set_xticks(range(len(pivot_table.columns)))
        ax7.set_yticks(range(len(pivot_table.index)))
        ax7.set_xticklabels(pivot_table.columns)
        ax7.set_yticklabels(pivot_table.index)
        ax7.set_xlabel('Processos MPI', fontsize=10)
        ax7.set_ylabel('Threads OpenMP', fontsize=10)
        ax7.set_title(f'7. Heatmap GFLOPS - {main_size}×{main_size}', fontsize=11, fontweight='bold')
        
        # Adicionar valores nas células
        for i in range(len(pivot_table.index)):
            for j in range(len(pivot_table.columns)):
                val = pivot_table.iloc[i, j]
                if not np.isnan(val):
                    ax7.text(j, i, f'{val:.2f}', ha='center', va='center', 
                            color='white' if val > pivot_table.max().max()/2 else 'black',
                            fontsize=8, fontweight='bold')
        
        plt.colorbar(im, ax=ax7, label='GFLOPS')
    
    # 8. Heatmap de Efficiency (Processos vs Threads)
    ax8 = plt.subplot(4, 3, 8)
    
    pivot_eff = df[df['MatrixSize'] == main_size].groupby(['NumProcesses', 'NumThreads'])['Efficiency(%)'].mean().reset_index()
    pivot_eff_table = pivot_eff.pivot(index='NumThreads', columns='NumProcesses', values='Efficiency(%)')
    
    if not pivot_eff_table.empty:
        im2 = ax8.imshow(pivot_eff_table, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
        ax8.set_xticks(range(len(pivot_eff_table.columns)))
        ax8.set_yticks(range(len(pivot_eff_table.index)))
        ax8.set_xticklabels(pivot_eff_table.columns)
        ax8.set_yticklabels(pivot_eff_table.index)
        ax8.set_xlabel('Processos MPI', fontsize=10)
        ax8.set_ylabel('Threads OpenMP', fontsize=10)
        ax8.set_title(f'8. Heatmap Efficiency - {main_size}×{main_size}', fontsize=11, fontweight='bold')
        
        # Adicionar valores nas células
        for i in range(len(pivot_eff_table.index)):
            for j in range(len(pivot_eff_table.columns)):
                val = pivot_eff_table.iloc[i, j]
                if not np.isnan(val):
                    ax8.text(j, i, f'{val:.1f}%', ha='center', va='center', 
                            color='white' if val < 50 else 'black',
                            fontsize=8, fontweight='bold')
        
        plt.colorbar(im2, ax=ax8, label='Efficiency (%)')
    
    # 9. Escalabilidade (Speedup Real vs Ideal) - POR TAMANHO
    ax9 = plt.subplot(4, 3, 9)
    
    sizes = sorted(df['MatrixSize'].unique())
    colors_scale = ['blue', 'red', 'green', 'orange', 'purple']
    
    for idx, size in enumerate(sizes):
        data_size = df[df['MatrixSize'] == size].sort_values('TotalCores')
        if len(data_size) > 1:
            color = colors_scale[idx % len(colors_scale)]
            ax9.plot(data_size['TotalCores'], data_size['Speedup'], 
                    marker='o', linewidth=2, markersize=8, 
                    label=f'{size}×{size}', color=color)
    
    # Linha de speedup ideal (linear) - apenas uma vez
    if len(df) > 0:
        max_cores = df['TotalCores'].max()
        ideal_cores = np.arange(1, max_cores + 1)
        ax9.plot(ideal_cores, ideal_cores, 'k--', linewidth=2, 
                label='Ideal (Linear)', alpha=0.5, zorder=0)
    
    ax9.set_xlabel('Total de Cores', fontsize=10)
    ax9.set_ylabel('Speedup', fontsize=10)
    ax9.set_title('9. Escalabilidade por Tamanho', fontsize=11, fontweight='bold')
    ax9.legend(fontsize=8)
    ax9.grid(True, alpha=0.3)
    ax9.set_xscale('log', base=2)
    ax9.set_yscale('log', base=2)
    
    # 10. Distribuição de GFLOPS (boxplot)
    ax10 = plt.subplot(4, 3, 10)
    # 10. Distribuição de GFLOPS (boxplot)
    ax10 = plt.subplot(4, 3, 10)
    sizes = sorted(df['MatrixSize'].unique())
    gflops_by_size = [df[df['MatrixSize'] == size]['GFLOPS'].values for size in sizes]
    
    # Criar labels mais informativos
    labels = []
    for size in sizes:
        size_data = df[df['MatrixSize'] == size]
        n_tests = len(size_data)
        labels.append(f'{size}\n({n_tests} testes)')
    
    bp = ax10.boxplot(gflops_by_size, labels=labels, patch_artist=True)
    
    # Colorir boxes diferentes para cada tamanho
    colors = ['lightblue', 'lightcoral', 'lightgreen', 'lightyellow', 'lightpink']
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
    
    ax10.set_xlabel('Tamanho da Matriz', fontsize=10)
    ax10.set_ylabel('GFLOPS', fontsize=10)
    ax10.set_title('10. Distribuição de Performance', fontsize=11, fontweight='bold')
    ax10.grid(True, alpha=0.3, axis='y')
    plt.setp(ax10.xaxis.get_majorticklabels(), rotation=0, fontsize=8)
    
    # 11. Melhor Configuração por Tamanho
    ax11 = plt.subplot(4, 3, 11)
    # 11. Melhor Configuração por Tamanho
    ax11 = plt.subplot(4, 3, 11)
    best_configs = []
    for size in sorted(df['MatrixSize'].unique()):
        size_data = df[df['MatrixSize'] == size]
        best = size_data.loc[size_data['GFLOPS'].idxmax()]
        best_configs.append({
            'size': size,
            'gflops': best['GFLOPS'],
            'config': f"{int(best['NumProcesses'])}P×{int(best['NumThreads'])}T"
        })
    
    if best_configs:
        sizes = [c['size'] for c in best_configs]
        gflops = [c['gflops'] for c in best_configs]
        configs = [c['config'] for c in best_configs]
        
        bars = ax11.bar(range(len(sizes)), gflops, color='green', alpha=0.7)
        ax11.set_xticks(range(len(sizes)))
        ax11.set_xticklabels([f'{s}' for s in sizes])
        ax11.set_xlabel('Tamanho da Matriz', fontsize=10)
        ax11.set_ylabel('GFLOPS', fontsize=10)
        ax11.set_title('11. Melhor Performance por Tamanho', fontsize=11, fontweight='bold')
        ax11.grid(True, alpha=0.3, axis='y')
        
        # Adicionar labels com configurações
        for i, (bar, config) in enumerate(zip(bars, configs)):
            height = bar.get_height()
            ax11.text(bar.get_x() + bar.get_width()/2., height,
                    f'{config}\n{gflops[i]:.2f}',
                    ha='center', va='bottom', fontsize=7)
    
    # 12. Tabela de Resumo
    ax12 = plt.subplot(4, 3, 12)
    # 12. Tabela de Resumo POR TAMANHO
    ax12 = plt.subplot(4, 3, 12)
    ax12.axis('tight')
    ax12.axis('off')
    
    # Criar tabela com estatísticas por tamanho de matriz
    summary_data = []
    sizes = sorted(df['MatrixSize'].unique())
    
    # Cabeçalho
    if len(sizes) == 2:
        summary_data.append(['Métrica', f'{sizes[0]}×{sizes[0]}', f'{sizes[1]}×{sizes[1]}'])
        col_widths = [0.35, 0.325, 0.325]
        colors = [['lightgray', 'lightgray', 'lightgray']]
    else:
        # Se houver mais ou menos tamanhos, usar formato mais genérico
        header = ['Métrica'] + [f'{s}×{s}' for s in sizes]
        summary_data.append(header)
        col_widths = [0.3] + [0.7 / len(sizes)] * len(sizes)
        colors = [['lightgray'] * (len(sizes) + 1)]
    
    # Dados por linha
    metrics = []
    
    # GFLOPS
    gflops_vals = [f"{df[df['MatrixSize'] == s]['GFLOPS'].max():.2f}" for s in sizes]
    metrics.append(['GFLOPS Máx'] + gflops_vals)
    
    # Speedup
    speedup_vals = [f"{df[df['MatrixSize'] == s]['Speedup'].max():.2f}x" for s in sizes]
    metrics.append(['Speedup Máx'] + speedup_vals)
    
    # Efficiency
    eff_vals = [f"{df[df['MatrixSize'] == s]['Efficiency(%)'].max():.1f}%" for s in sizes]
    metrics.append(['Eff. Máxima'] + eff_vals)
    
    # Separador
    metrics.append(['─────────'] + ['─────────'] * len(sizes))
    
    # Melhor config
    best_configs_str = []
    for s in sizes:
        size_data = df[df['MatrixSize'] == s]
        best = size_data.loc[size_data['GFLOPS'].idxmax()]
        best_configs_str.append(f"{int(best['NumProcesses'])}P×{int(best['NumThreads'])}T")
    metrics.append(['Melhor Cfg'] + best_configs_str)
    
    # Número de testes
    n_tests = [f"{len(df[df['MatrixSize'] == s])}" for s in sizes]
    metrics.append(['# Testes'] + n_tests)
    
    # Separador
    metrics.append(['─────────'] + ['─────────'] * len(sizes))
    
    # Médias
    gflops_avg = [f"{df[df['MatrixSize'] == s]['GFLOPS'].mean():.2f}" for s in sizes]
    metrics.append(['GFLOPS Méd'] + gflops_avg)
    
    speedup_avg = [f"{df[df['MatrixSize'] == s]['Speedup'].mean():.2f}x" for s in sizes]
    metrics.append(['Speedup Méd'] + speedup_avg)
    
    eff_avg = [f"{df[df['MatrixSize'] == s]['Efficiency(%)'].mean():.1f}%" for s in sizes]
    metrics.append(['Eff. Média'] + eff_avg)
    
    summary_data.extend(metrics)
    
    # Cores alternadas
    row_colors = []
    for i in range(len(summary_data)):
        if i == 0:
            continue  # Já adicionado
        elif '─────────' in summary_data[i][0]:
            row_colors.append(['lightgray'] * (len(sizes) + 1))
        else:
            row_colors.append(['white'] + ['lightyellow'] * len(sizes))
    
    colors.extend(row_colors)
    
    table = ax12.table(cellText=summary_data, cellLoc='center',
                     colWidths=col_widths, loc='center',
                     cellColours=colors)
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2.2)
    ax12.set_title('12. Resumo Estatístico por Tamanho', fontsize=11, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Salvar figura
    output_file = 'matrix_giant_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfico salvo em: {output_file}")
    
    # Exibir estatísticas no console - POR TAMANHO
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║          RESUMO DAS MÉTRICAS POR TAMANHO - GIGANTES          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"Total de testes realizados: {len(df)}\n")
    
    # Estatísticas por tamanho de matriz
    sizes = sorted(df['MatrixSize'].unique())
    
    for size in sizes:
        size_data = df[df['MatrixSize'] == size]
        best_row = size_data.loc[size_data['GFLOPS'].idxmax()]
        
        print(f"{'='*63}")
        print(f"📐 MATRIZ {size}×{size} ({len(size_data)} testes)")
        print(f"{'='*63}")
        
        print(f"\n🏆 Melhor Performance:")
        print(f"  GFLOPS: {best_row['GFLOPS']:.2f}")
        print(f"  Configuração: {int(best_row['NumProcesses'])}P × {int(best_row['NumThreads'])}T")
        print(f"  Tempo: {best_row['ParTime(s)']:.2f}s")
        print(f"  Speedup: {best_row['Speedup']:.2f}x")
        print(f"  Efficiency: {best_row['Efficiency(%)']:.1f}%")
        
        print(f"\n📊 Estatísticas:")
        print(f"  GFLOPS: máx={size_data['GFLOPS'].max():.2f}, "
              f"méd={size_data['GFLOPS'].mean():.2f}, "
              f"mín={size_data['GFLOPS'].min():.2f}")
        print(f"  Speedup: máx={size_data['Speedup'].max():.2f}x, "
              f"méd={size_data['Speedup'].mean():.2f}x, "
              f"mín={size_data['Speedup'].min():.2f}x")
        print(f"  Efficiency: máx={size_data['Efficiency(%)'].max():.1f}%, "
              f"méd={size_data['Efficiency(%)'].mean():.1f}%, "
              f"mín={size_data['Efficiency(%)'].min():.1f}%")
        print(f"  Tempo: seq={size_data.iloc[0]['SeqTime(s)']:.2f}s, "
              f"par_mín={size_data['ParTime(s)'].min():.2f}s, "
              f"par_máx={size_data['ParTime(s)'].max():.2f}s")
        
        print(f"\n🥇 Top 3 Configurações ({size}×{size}):")
        top3 = size_data.nlargest(3, 'GFLOPS')[['NumProcesses', 'NumThreads', 'GFLOPS', 'Speedup', 'Efficiency(%)']]
        for idx, row in top3.iterrows():
            print(f"  {int(row['NumProcesses'])}P×{int(row['NumThreads'])}T: "
                  f"{row['GFLOPS']:.2f} GFLOPS | "
                  f"Speedup {row['Speedup']:.2f}x | "
                  f"Eff. {row['Efficiency(%)']:.1f}%")
        print()
    
    print("═══════════════════════════════════════════════════════════════")
    
    # Mostrar gráfico
    try:
        plt.show()
    except:
        print("\nℹ️  Não foi possível exibir o gráfico interativamente.")
        print(f"   Visualize o arquivo: {output_file}")

if __name__ == '__main__':
    csv_file = 'matrix_giant_metrics.csv'
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║    Análise de Performance - Matrizes GIGANTES                 ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    plot_giant_speedup(csv_file)
