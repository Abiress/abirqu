package abirqu

import (
	"math"
	"testing"
)

func TestCreateSimulator(t *testing.T) {
	sim := CreateSimulator(2)
	if sim == nil {
		t.Fatal("Failed to create simulator")
	}
	defer sim.Destroy()

	if sim.NumQubits() != 2 {
		t.Errorf("Expected 2 qubits, got %d", sim.NumQubits())
	}
	if sim.HilbertDim() != 4 {
		t.Errorf("Expected dim 4, got %d", sim.HilbertDim())
	}
}

func TestBellState(t *testing.T) {
	sim := CreateBellState()
	defer sim.Destroy()

	probs := sim.GetProbabilities()

	if math.Abs(probs[0]-0.5) > 1e-10 {
		t.Errorf("Expected |00> prob 0.5, got %f", probs[0])
	}
	if math.Abs(probs[3]-0.5) > 1e-10 {
		t.Errorf("Expected |11> prob 0.5, got %f", probs[3])
	}
	if math.Abs(probs[1]) > 1e-10 {
		t.Errorf("Expected |01> prob 0, got %f", probs[1])
	}
	if math.Abs(probs[2]) > 1e-10 {
		t.Errorf("Expected |10> prob 0, got %f", probs[2])
	}
}

func TestSingleQubitGates(t *testing.T) {
	sim := CreateSimulator(1)
	defer sim.Destroy()

	sim.H(0)
	probs := sim.GetProbabilities()

	if math.Abs(probs[0]-0.5) > 1e-10 {
		t.Errorf("Expected 50%% |0>, got %f", probs[0])
	}
	if math.Abs(probs[1]-0.5) > 1e-10 {
		t.Errorf("Expected 50%% |1>, got %f", probs[1])
	}
}

func TestRotationGates(t *testing.T) {
	sim := CreateSimulator(1)
	defer sim.Destroy()

	sim.RX(0, math.Pi)
	probs := sim.GetProbabilities()

	if math.Abs(probs[1]-1.0) > 1e-10 {
		t.Errorf("Expected RX(π) to give |1>, got %f", probs[1])
	}
}

func TestStatevector(t *testing.T) {
	sim := CreateBellState()
	defer sim.Destroy()

	state := sim.GetStatevector()
	expectedLen := 8 // 4 complex numbers * 2 (re, im)
	if len(state) != expectedLen {
		t.Errorf("Expected state length %d, got %d", expectedLen, len(state))
	}

	// Bell state: (|00> + |11>)/sqrt(2)
	expected := 1.0 / math.Sqrt(2)
	if math.Abs(state[0]-expected) > 1e-10 {
		t.Errorf("Expected re(|00>) = %f, got %f", expected, state[0])
	}
}

func TestRunCircuit(t *testing.T) {
	sim := CreateSimulator(2)
	defer sim.Destroy()

	gates := []Gate{
		{GateH, 0, 0, 0},
		{GateCNOT, 0, 1, 0},
	}
	sim.RunCircuit(gates)

	probs := sim.GetProbabilities()
	if math.Abs(probs[0]-0.5) > 1e-10 {
		t.Errorf("Expected Bell state |00> prob 0.5, got %f", probs[0])
	}
}
