use rand::Rng;

pub struct NeuralNetwork {
    input_size: usize,
    hidden_size: usize,
    output_size: usize,
    learning_rate: f64,
    weights_input_hidden: Vec<Vec<f64>>,
    weights_hidden_output: Vec<Vec<f64>>,
    bias_hidden: Vec<f64>,
    bias_output: Vec<f64>,
}

impl NeuralNetwork {
    pub fn new(input_size: usize, hidden_size: usize, output_size: usize, learning_rate: f64) -> Self {
        let mut rng = rand::thread_rng();
        let weights_input_hidden = (0..hidden_size)
            .map(|_| (0..input_size).map(|_| rng.gen_range(-1.0..1.0)).collect())
            .collect();
        let weights_hidden_output = (0..output_size)
            .map(|_| (0..hidden_size).map(|_| rng.gen_range(-1.0..1.0)).collect())
            .collect();
        let bias_hidden = vec![0.0; hidden_size];
        let bias_output = vec![0.0; output_size];
        NeuralNetwork {
            input_size,
            hidden_size,
            output_size,
            learning_rate,
            weights_input_hidden,
            weights_hidden_output,
            bias_hidden,
            bias_output,
        }
    }

    fn sigmoid(x: f64) -> f64 {
        1.0 / (1.0 + (-x).exp())
    }

    fn sigmoid_derivative(x: f64) -> f64 {
        x * (1.0 - x)
    }

    pub fn forward(&self, input: &[f64]) -> (Vec<f64>, Vec<f64>) {
        let hidden: Vec<f64> = self
            .weights_input_hidden
            .iter()
            .zip(self.bias_hidden.iter())
            .map(|(w, b)| {
                let sum: f64 = w.iter().zip(input.iter()).map(|(wi, xi)| wi * xi).sum();
                Self::sigmoid(sum + b)
            })
            .collect();

        let output: Vec<f64> = self
            .weights_hidden_output
            .iter()
            .zip(self.bias_output.iter())
            .map(|(w, b)| {
                let sum: f64 = w.iter().zip(hidden.iter()).map(|(wi, hi)| wi * hi).sum();
                Self::sigmoid(sum + b)
            })
            .collect();

        (hidden, output)
    }

    pub fn train(&mut self, input: &[f64], target: &[f64]) {
        let (hidden, output) = self.forward(&input);

        // Calculate output errors
        let output_errors: Vec<f64> = target
            .iter()
            .zip(output.iter())
            .map(|(t, o)| t - o)
            .collect();

        // Calculate output deltas
        let output_deltas: Vec<f64> = output_errors
            .iter()
            .zip(output.iter())
            .map(|(e, o)| e * Self::sigmoid_derivative(*o))
            .collect();

        // Calculate hidden errors
        let hidden_errors: Vec<f64> = self
            .weights_hidden_output
            .iter()
            .zip(output_deltas.iter())
            .map(|(w, od)| w.iter().map(move |wi| wi * od).sum())
            .collect();

        // Calculate hidden deltas
        let hidden_deltas: Vec<f64> = hidden_errors
            .iter()
            .zip(hidden.iter())
            .map(|(e, h)| e * Self::sigmoid_derivative(*h))
            .collect();

        // Update weights_hidden_output
        for (i, weights) in self.weights_hidden_output.iter_mut().enumerate() {
            for (j, weight) in weights.iter_mut().enumerate() {
                *weight += self.learning_rate * output_deltas[i] * hidden[j];
            }
        }

        // Update bias_output
        for (i, b) in self.bias_output.iter_mut().enumerate() {
            *b += self.learning_rate * output_deltas[i];
        }

        // Update weights_input_hidden
        for (i, weights) in self.weights_input_hidden.iter_mut().enumerate() {
            for (j, weight) in weights.iter_mut().enumerate() {
                *weight += self.learning_rate * hidden_deltas[i] * input[j];
            }
        }

        // Update bias_hidden
        for (i, b) in self.bias_hidden.iter_mut().enumerate() {
            *b += self.learning_rate * hidden_deltas[i];
        }
    }

    pub fn predict(&self, input: &[f64]) -> Vec<f64> {
        let (_, output) = self.forward(&input);
        output
    }
    
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_neural_network() {
        // Create a new neural network with 9 input nodes, 10 hidden nodes, and 9 output nodes
        let mut nn = NeuralNetwork::new(9, 10, 9, 0.1);
        // Define the input vector with 9 elements, all set to 0.0
        let input = vec![0.0; 9];
        // Define the target vector with 9 elements, all set to 1.0
        let target = vec![1.0; 9];
        // Train the neural network with the input and target vectors
        nn.train(&input, &target);
        // Predict the output using the same input vector
        let output = nn.predict(&input);
        // Check that the output vector has 9 elements
        assert_eq!(output.len(), 9);
        assert_eq!(output.len(), 9);

        // Use other methods to avoid unused warnings
        let _ = NeuralNetwork::sigmoid(0.5);
        let _ = NeuralNetwork::sigmoid_derivative(0.5);
        let _ = nn.forward(&input);
    }
}