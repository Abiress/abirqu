import com.abirqu.AbirQuSimulator;

/**
 * Test suite for AbirQu Java JNI wrapper
 */
public class TestAbirQu {
    
    static int passed = 0;
    static int failed = 0;
    
    static void assertTrue(boolean condition, String testName) {
        if (condition) {
            System.out.println("✓ " + testName);
            passed++;
        } else {
            System.out.println("✗ " + testName);
            failed++;
        }
    }
    
    static void assertClose(double a, double b, double tolerance, String testName) {
        if (Math.abs(a - b) < tolerance) {
            System.out.println("✓ " + testName);
            passed++;
        } else {
            System.out.println("✗ " + testName + " (expected " + b + ", got " + a + ")");
            failed++;
        }
    }
    
    public static void main(String[] args) {
        System.out.println("Running AbirQu Java JNI Tests...\n");
        
        // Test 1: Create simulator
        System.out.println("--- Lifecycle ---");
        AbirQuSimulator sim = new AbirQuSimulator(2);
        assertTrue(sim.getNumQubits() == 2, "Create 2-qubit simulator");
        assertTrue(sim.getHilbertDim() == 4, "Hilbert dimension is 4");
        
        // Test 2: Bell state
        System.out.println("\n--- Bell State ---");
        AbirQuSimulator bell = AbirQuSimulator.createBellState();
        double[] probs = bell.getProbabilities();
        assertClose(probs[0], 0.5, 1e-10, "Bell state |00> probability");
        assertClose(probs[3], 0.5, 1e-10, "Bell state |11> probability");
        assertClose(probs[1], 0.0, 1e-10, "Bell state |01> probability");
        assertClose(probs[2], 0.0, 1e-10, "Bell state |10> probability");
        
        // Test 3: Single qubit gates
        System.out.println("\n--- Single Qubit Gates ---");
        AbirQuSimulator sim2 = new AbirQuSimulator(1);
        sim2.h(0);
        probs = sim2.getProbabilities();
        assertClose(probs[0], 0.5, 1e-10, "H|0> gives 50% |0>");
        assertClose(probs[1], 0.5, 1e-10, "H|0> gives 50% |1>");
        
        // Test 4: Rotation gates
        System.out.println("\n--- Rotation Gates ---");
        AbirQuSimulator sim3 = new AbirQuSimulator(1);
        sim3.rx(0, Math.PI);
        probs = sim3.getProbabilities();
        assertClose(probs[1], 1.0, 1e-10, "RX(π) rotates to |1>");
        
        // Test 5: State vector
        System.out.println("\n--- State Vector ---");
        AbirQuSimulator sim4 = AbirQuSimulator.createBellState();
        double[] state = sim4.getStatevector();
        assertTrue(state.length == 8, "State vector has 8 elements (4 complex)");
        assertClose(state[0], 1.0/Math.sqrt(2), 1e-10, "Bell state real part of |00>");
        
        // Cleanup
        sim.close();
        bell.close();
        sim2.close();
        sim3.close();
        sim4.close();
        
        System.out.println("\n--- Results ---");
        System.out.println("Passed: " + passed);
        System.out.println("Failed: " + failed);
        System.out.println("Total: " + (passed + failed));
        
        if (failed > 0) {
            System.exit(1);
        } else {
            System.out.println("\nAll tests passed! ✓");
        }
    }
}
