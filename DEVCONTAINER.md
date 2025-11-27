# Como usar o DevContainer

1. Abra a pasta no VS Code.
2. Clique em "Reopen in Container" (ícone verde no canto inferior esquerdo).
3. O container será construído usando `.devcontainer/devcontainer.json`.
4. Após a criação, o comando `make` será executado automaticamente (compila `bin/hello`).

## Compilar e executar

### Versão básica (sem paralelismo)
```bash
make run
```

### OpenMP (paralelismo em memória compartilhada)
```bash
make run-omp
```

### MPI (paralelismo distribuído)
```bash
make run-mpi
```

### Híbrido (MPI + OpenMP)
```bash
make run-hybrid
```

## Dependências instaladas
- **GCC**: compilador C com suporte a OpenMP (`-fopenmp`)
- **Open MPI**: implementação de MPI para programação paralela distribuída
- **make**: ferramenta de build

## Observações
- O `postCreateCommand` já executa `make`; se quiser recompilar, rode `make` manualmente.
- Número de processos MPI pode ser ajustado no Makefile (flag `-np`).
