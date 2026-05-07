// Package abirqu provides Go bindings for the AbirQu quantum simulator.
//
// It uses cgo to call the C ABI exposed by libabirqu_core.so.
//
// Usage:
//
//	import "github.com/abirqu/abirqu"
//
//	sim := abirqu.CreateSimulator(2)
//	defer sim.Destroy()
//	sim.H(0)
//	sim.CNOT(0, 1)
//	probs := sim.GetProbabilities()
package abirqu

/*
#cgo CFLAGS: -I${SRCDIR}/../../jni/include
#cgo LDFLAGS: -L${SRCDIR}/../../target/release -labirqu_core

#include <stdlib.h>
#include "abirqu.h"
*/
import "C"
import (
	"unsafe"
)

// Gate constants
const (
	GateH    = 0
	GateX    = 1
	GateY    = 2
	GateZ    = 3
	GateS    = 4
	GateT    = 5
	GateCNOT = 6
	GateCZ   = 7
	GateRX   = 8
	GateRY   = 9
	GateRZ   = 10
	GateSWAP = 11
)

// Simulator wraps the C AbirQuSimulator handle
type Simulator struct {
	handle *C.AbirQuSimulator
}

// CreateSimulator creates a new simulator for numQubits qubits
func CreateSimulator(numQubits uint32) *Simulator {
	handle := C.abirqu_simulator_create(C.uint32_t(numQubits))
	if handle == nil {
		return nil
	}
	return &Simulator{handle: handle}
}

// Destroy frees the simulator
func (s *Simulator) Destroy() {
	if s.handle != nil {
		C.abirqu_simulator_destroy(s.handle)
		s.handle = nil
	}
}

// Reset resets simulator to |0...0>
func (s *Simulator) Reset() {
	C.abirqu_simulator_reset(s.handle)
}

// NumQubits returns the number of qubits
func (s *Simulator) NumQubits() uint32 {
	return uint32(C.abirqu_num_qubits(s.handle))
}

// HilbertDim returns 2^numQubits
func (s *Simulator) HilbertDim() uint {
	return uint(C.abirqu_hilbert_dim(s.handle))
}

// Gate operations
func (s *Simulator) H(q uint32) {
	C.abirqu_h(s.handle, C.uint32_t(q))
}

func (s *Simulator) X(q uint32) {
	C.abirqu_x(s.handle, C.uint32_t(q))
}

func (s *Simulator) Y(q uint32) {
	C.abirqu_y(s.handle, C.uint32_t(q))
}

func (s *Simulator) Z(q uint32) {
	C.abirqu_z(s.handle, C.uint32_t(q))
}

func (s *Simulator) S(q uint32) {
	C.abirqu_s(s.handle, C.uint32_t(q))
}

func (s *Simulator) T(q uint32) {
	C.abirqu_t(s.handle, C.uint32_t(q))
}

func (s *Simulator) RX(q uint32, angle float64) {
	C.abirqu_rx(s.handle, C.uint32_t(q), C.double(angle))
}

func (s *Simulator) RY(q uint32, angle float64) {
	C.abirqu_ry(s.handle, C.uint32_t(q), C.double(angle))
}

func (s *Simulator) RZ(q uint32, angle float64) {
	C.abirqu_rz(s.handle, C.uint32_t(q), C.double(angle))
}

func (s *Simulator) CNOT(ctrl, target uint32) {
	C.abirqu_cnot(s.handle, C.uint32_t(ctrl), C.uint32_t(target))
}

func (s *Simulator) CZ(ctrl, target uint32) {
	C.abirqu_cz(s.handle, C.uint32_t(ctrl), C.uint32_t(target))
}

func (s *Simulator) SWAP(q0, q1 uint32) {
	C.abirqu_swap(s.handle, C.uint32_t(q0), C.uint32_t(q1))
}

// GetProbabilities returns measurement probabilities
func (s *Simulator) GetProbabilities() []float64 {
	dim := s.HilbertDim()
	probs := make([]float64, dim)
	C.abirqu_get_probabilities(s.handle, (*C.double)(unsafe.Pointer(&probs[0])))
	return probs
}

// GetStatevector returns the state vector as interleaved [re, im, re, im, ...]
func (s *Simulator) GetStatevector() []float64 {
	dim := s.HilbertDim()
	re := make([]float64, dim)
	im := make([]float64, dim)
	C.abirqu_get_statevector(
		s.handle,
		(*C.double)(unsafe.Pointer(&re[0])),
		(*C.double)(unsafe.Pointer(&im[0])),
	)
	state := make([]float64, dim*2)
	for i := uint(0); i < dim; i++ {
		state[i*2] = re[i]
		state[i*2+1] = im[i]
	}
	return state
}

// Gate represents a quantum gate for batch execution
type Gate struct {
	GateType uint8
	Ctrl     uint32
	Target    uint32
	Param     float64
}

// RunCircuit executes a batch of gates
func (s *Simulator) RunCircuit(gates []Gate) {
	n := len(gates)
	if n == 0 {
		return
	}
	// Convert to C gates
	cGates := make([]C.AbirQuGate, n)
	for i, g := range gates {
		cGates[i].gate_type = C.uint8_t(g.GateType)
		cGates[i].ctrl = C.uint32_t(g.Ctrl)
		cGates[i].target = C.uint32_t(g.Target)
		cGates[i].param = C.double(g.Param)
	}
	C.abirqu_run_circuit(s.handle, &cGates[0], C.size_t(n))
}

// CreateBellState creates a Bell state |00> + |11>
func CreateBellState() *Simulator {
	sim := CreateSimulator(2)
	sim.H(0)
	sim.CNOT(0, 1)
	return sim
}
