CC = gcc
MPICC = mpicc
CFLAGS = -Wall -Wextra -O2
OMPFLAGS = -fopenmp
MPIFLAGS = -Wall -Wextra -O2
SRC = src/main.c
BIN_DIR = bin
TARGET = $(BIN_DIR)/hello
TARGET_OMP = $(BIN_DIR)/hello_omp
TARGET_MPI = $(BIN_DIR)/hello_mpi
TARGET_HYBRID = $(BIN_DIR)/hello_hybrid

all: $(TARGET)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(TARGET): | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

omp: | $(BIN_DIR)
	$(CC) $(CFLAGS) $(OMPFLAGS) -o $(TARGET_OMP) $(SRC)

mpi: | $(BIN_DIR)
	$(MPICC) $(MPIFLAGS) -o $(TARGET_MPI) $(SRC)

hybrid: | $(BIN_DIR)
	$(MPICC) $(MPIFLAGS) $(OMPFLAGS) -o $(TARGET_HYBRID) $(SRC)

run: all
	./$(TARGET)

run-omp: omp
	./$(TARGET_OMP)

run-mpi: mpi
	mpirun -np 4 $(TARGET_MPI)

run-hybrid: hybrid
	mpirun -np 2 $(TARGET_HYBRID)

clean:
	rm -rf $(BIN_DIR)

.PHONY: all omp mpi hybrid run run-omp run-mpi run-hybrid clean
