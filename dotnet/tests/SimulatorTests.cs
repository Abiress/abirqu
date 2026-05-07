using System;
using Xunit;

namespace AbirQu.Tests
{
    public class SimulatorTests
    {
        [Fact]
        public void TestCreateSimulator()
        {
            var sim = new Simulator(2);
            Assert.Equal((uint)2, sim.NumQubits);
            Assert.Equal((ulong)4, sim.HilbertDim);
            sim.Dispose();
        }

        [Fact]
        public void TestBellState()
        {
            var sim = Simulator.CreateBellState();
            var probs = sim.GetProbabilities();
            
            Assert.True(Math.Abs(probs[0] - 0.5) < 1e-10);
            Assert.True(Math.Abs(probs[3] - 0.5) < 1e-10);
            Assert.True(Math.Abs(probs[1]) < 1e-10);
            Assert.True(Math.Abs(probs[2]) < 1e-10);
            
            sim.Dispose();
        }

        [Fact]
        public void TestSingleQubitGates()
        {
            var sim = new Simulator(1);
            sim.H(0);
            var probs = sim.GetProbabilities();
            
            Assert.True(Math.Abs(probs[0] - 0.5) < 1e-10);
            Assert.True(Math.Abs(probs[1] - 0.5) < 1e-10);
            
            sim.Dispose();
        }

        [Fact]
        public void TestRotationGates()
        {
            var sim = new Simulator(1);
            sim.RX(0, Math.PI);
            var probs = sim.GetProbabilities();
            
            Assert.True(Math.Abs(probs[1] - 1.0) < 1e-10);
            
            sim.Dispose();
        }

        [Fact]
        public void TestStatevector()
        {
            var sim = Simulator.CreateBellState();
            var state = sim.GetStatevector();
            
            Assert.Equal(8, state.Length); // 4 complex numbers * 2
            var expected = 1.0 / Math.Sqrt(2);
            Assert.True(Math.Abs(state[0] - expected) < 1e-10);
            
            sim.Dispose();
        }
    }
}
