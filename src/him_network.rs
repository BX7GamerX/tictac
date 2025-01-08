use rand::Rng;

pub struct HimNetwork {
    //  layer : connections : nodes
    //weights
    //The weights are stored in 3D arrays
    //The first dimension represents the layer
    //The second dimension represents the connections
    //The third dimension represents the nodes
    pub w: Vec<Vec<Vec<f32>>>,
    
    
    pub x1: Vec<Vec<f32>>, // 10000 games
    //biases
    //The biases are stored in 2D arrays
    //The first dimension represents the layer
    //The second dimension represents the nodes
    pub b: Vec<Vec<f32>>,


    
    //forawrd propagation parameters
    pub z : Vec<Vec<Vec<f32>>>,
    pub a : Vec<Vec<Vec<f32>>>,

    pub dW: Vec<Vec<Vec<f32>>>,
    pub db: Vec<Vec<f32>>,

}

impl HimNetwork {
    pub fn new() -> HimNetwork {
        HimNetwork {
            x1: vec![vec![0.0; 9]; 10000],
            w: vec![
                vec![vec![0.0; 9]; 81],     // layer 1
                vec![vec![0.0; 81]; 81],   // layer 2
                vec![vec![0.0; 81]; 81],   // layer 3
                vec![vec![0.0; 81]; 81],   // adjust if needed
                vec![vec![0.0; 9]; 81],    // final layer => 9 outputs
            ],
            b: vec![
                vec![0.0; 81], 
                vec![0.0; 81],
                vec![0.0; 81], 
                vec![0.0; 81],
                vec![0.0; 9],             // final layer => 9 biases
            ],
            z: vec![
                vec![vec![0.0; 9]; 81],   
                vec![vec![0.0; 81]; 10000], // reorder to match dims
                vec![vec![0.0; 81]; 10000],
                vec![vec![0.0; 81]; 10000],
                vec![vec![0.0; 9]; 10000],  // final => 9 columns
            ],
            a: vec![
                // same shape as z
                vec![vec![0.0; 9]; 81],
                vec![vec![0.0; 81]; 10000],
                vec![vec![0.0; 81]; 10000],
                vec![vec![0.0; 81]; 10000],
                vec![vec![0.0; 9]; 10000],  // final => 9 columns
            ],
            dW: vec![
                vec![vec![0.0; 9]; 81],
                vec![vec![0.0; 81]; 81],
                vec![vec![0.0; 81]; 81],
                vec![vec![0.0; 81]; 81],
                vec![vec![0.0; 9]; 81],
            ],
            db: vec![
                vec![0.0; 81],
                vec![0.0; 81],
                vec![0.0; 81],
                vec![0.0; 81],
                vec![0.0; 9],
            ],
        }
    }
    //Initialize the weights and biases
    //The weights are initialized with random values between -0.5 and 0.5
    //The biases are initialized with random values between 0 and 1
    //The weights and biases are stored in the network object
    //The weights are stored in 3D arrays
    //The first dimension represents the layer
    pub fn init_params(&mut self) {
        const CONNECTIONS_COUNT: usize = 9;
        const NODES_COUNT: usize = 81;
        // Initialize weights and biases
        for nodes in 0..NODES_COUNT {
            self.w[1][nodes] = vec![rand::thread_rng().gen_range(0.0..1.0) - 0.5; CONNECTIONS_COUNT];
            self.w[2][nodes] = vec![rand::thread_rng().gen_range(0.0..1.0) - 0.5; NODES_COUNT];
            self.w[3][nodes] = vec![rand::thread_rng().gen_range(0.0..1.0) - 0.5; NODES_COUNT];
            
            // Change final layer to 9 outputs instead of 81
            self.w[4][nodes] = vec![rand::thread_rng().gen_range(0.0..1.0) - 0.5; 9];

            self.b[1][nodes] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            self.b[2][nodes] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            self.b[3][nodes] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            
            // Also reduce the final bias dimension to 9
            self.b[4][nodes] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
        }
    }

    //Forward propagation
    pub fn forward_propagation(&mut self) {
        //First layer
        self.z[1] = self.ddd_matrix(self.multiply_matrix(&self.w[1], &self.x1), &self.b[1]);
        self.a[1] = self.ReLU(self.z[1].clone());
        //Second layer
        self.z[2] = self.ddd_matrix(self.multiply_matrix(&self.w[2], &self.a[1]), &self.b[2]);
        self.a[2] = self.ReLU(self.z[2].clone());
        //Third layer
        self.z[3] = self.ddd_matrix(self.multiply_matrix(&self.w[3], &self.a[2]), &self.b[3]);
        self.a[3] = self.ReLU(self.z[3].clone());
        //Fourth layer
        self.z[4] = self.ddd_matrix(self.multiply_matrix(&self.w[4], &self.a[3]), &self.b[4]);
        self.a[4] = self.softmax(&self.z[4]);
    }
    //One hot encode function
    //converts the class labels to one hot encoded vectors
    //the one hot encoded vectors are used to train the model
    pub fn one_hot_encode(&mut self,input: Vec<usize>, classes_count: usize) -> Vec<Vec<f32>> {
        let mut output = vec![vec![0.0; classes_count]; input.len()];
        for (i, &label) in input.iter().enumerate() {
            if label >= classes_count {
                panic!("Class label out of bounds");
            }
            output[i][label] = 1.0;
        }
        output
    }
    /*def backward_prop(Z1, A1, Z2, A2, Z3, A3, Z4, A4, W1, W2, W3, W4, X, Y):
    m = X.shape[1]  # Number of examples
    num_classes = A4.shape[0]  # Number of output classes
    
    # Convert labels Y to one-hot encoding
    one_hot_Y = one_hot(Y, num_classes)
    
    # Gradient for output layer
    dZ4 = A4 - one_hot_Y  # Loss gradient w.r.t Z4
    dW4 = 1 / m * np.dot(dZ4, A3.T)
    db4 = 1 / m * np.sum(dZ4, axis=1, keepdims=True)
    
    # Gradient for third layer
    dA3 = np.dot(W4.T, dZ4)
    dZ3 = dA3 * ReLU_deriv(Z3)  # Element-wise multiplication with ReLU derivative
    dW3 = 1 / m * np.dot(dZ3, A2.T)
    db3 = 1 / m * np.sum(dZ3, axis=1, keepdims=True)
    
    # Gradient for second layer
    dA2 = np.dot(W3.T, dZ3)
    dZ2 = dA2 * ReLU_deriv(Z2)
    dW2 = 1 / m * np.dot(dZ2, A1.T)
    db2 = 1 / m * np.sum(dZ2, axis=1, keepdims=True)
    
    # Gradient for first layer
    dA1 = np.dot(W2.T, dZ2)
    dZ1 = dA1 * ReLU_deriv(Z1)
    dW1 = 1 / m * np.dot(dZ1, X.T)
    db1 = 1 / m * np.sum(dZ1, axis=1, keepdims=True)
    
    */
    pub fn backward_propagation(&mut self, y: Vec<usize>) {
        let one_hot_y = self.one_hot_encode(y, 9);
        let m = 10000;
        let reciprocal_m = 1.0 / m as f32;

        // Gradient for output layer
        let mut dZ4 = vec![vec![0.0; self.a[4][0].len()]; self.a[4].len()];
        for i in 0..self.a[4].len() {
            for j in 0..self.a[4][i].len() {
                dZ4[i][j] = self.a[4][i][j] - one_hot_y[i][j];
            }
        }
        let a3_t = self.transpose(self.a[3].clone());
        let dZ4_a3_t = self.multiply_matrix(&dZ4, &a3_t);
        let dW4: Vec<Vec<f32>> = dZ4_a3_t
            .iter()
            .map(|row| row.iter().map(|val| val * reciprocal_m).collect())
            .collect();
        let db4 = self.sum_rows(&dZ4, reciprocal_m);

        // Gradient for third layer
        let w4_t = self.transpose(self.w[4].clone());
        let dA3 = self.multiply_matrix(&w4_t, &dZ4);
        let dZ3 = self.elementwise_multiply(&dA3, &self.relu_deriv(&self.z[3]));
        let a2_t = self.transpose(self.a[2].clone());
        let dZ3_a2_t = self.multiply_matrix(&dZ3, &a2_t);
        let dW3 = self.scale_matrix(dZ3_a2_t, reciprocal_m);
        let db3 = self.sum_rows(&dZ3, reciprocal_m);

        // Gradient for second layer
        let w3_t = self.transpose(self.w[3].clone());
        let dA2 = self.multiply_matrix(&w3_t, &dZ3);
        let dZ2 = self.elementwise_multiply(&dA2, &self.relu_deriv(&self.z[2]));
        let a1_t = self.transpose(self.a[1].clone());
        let dZ2_a1_t = self.multiply_matrix(&dZ2, &a1_t);
        let dW2 = self.scale_matrix(dZ2_a1_t, reciprocal_m);
        let db2 = self.sum_rows(&dZ2, reciprocal_m);

        // Gradient for first layer
        let w2_t = self.transpose(self.w[2].clone());
        let dA1 = self.multiply_matrix(&w2_t, &dZ2);
        let dZ1 = self.elementwise_multiply(&dA1, &self.relu_deriv(&self.z[1]));
        let x_t = self.transpose(self.x1.clone());
        let dZ1_x_t = self.multiply_matrix(&dZ1, &x_t);
        let dW1 = self.scale_matrix(dZ1_x_t, reciprocal_m);
        let db1 = self.sum_rows(&dZ1, reciprocal_m);

        self.dW  = vec![dW1, dW2, dW3, dW4];
        self.db = vec![db1, db2, db3, db4];
    }

    /*def update_params(W1, b1, W2, b2, W3, b3, W4, b4, 
                  dW1, db1, dW2, db2, dW3, db3, dW4, db4, alpha):
    # Update for Layer 1
    W1 = W1 - alpha * dW1
    b1 = b1 - alpha * db1

    # Update for Layer 2
    W2 = W2 - alpha * dW2
    b2 = b2 - alpha * db2

    # Update for Layer 3
    W3 = W3 - alpha * dW3
    b3 = b3 - alpha * db3

    # Update for Layer 4 (Output Layer)
    W4 = W4 - alpha * dW4
    b4 = b4 - alpha * db4

    return W1, b1, W2, b2, W3, b3, W4, b4
 */
    pub fn update_params(&mut self, alpha: f32) {
        for l in 0..self.w.len() {
            for i in 0..self.w[l].len() {
                for j in 0..self.w[l][i].len() {
                    self.w[l][i][j] -= alpha * self.dW[l][i][j];
                }
            }
            for i in 0..self.b[l].len() {
                self.b[l][i] -= alpha * self.db[l][i];
            }
        }
    }

    pub fn get_predictions(&self) -> Vec<usize> {
        let mut predictions = vec![];
        for i in 0..self.a[4].len() {
            let mut max_val = 0.0;
            let mut max_idx = 0;
            for j in 0..self.a[4][i].len() {
                if self.a[4][i][j] > max_val {
                    max_val = self.a[4][i][j];
                    max_idx = j;
                }
            }
            predictions.push(max_idx);
        }
        predictions
    }
    pub fn gradient_descent(&mut self, y: Vec<usize>, alpha: f32, num_games: usize) {
        self.init_params();
        self.forward_propagation();
        self.backward_propagation(y);
        self.update_params(alpha);
    }
    pub fn transpose(&mut self,matrix: Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        if matrix.is_empty() || matrix[0].is_empty() {
            return vec![];
        }
    
        let rows = matrix.len();
        let cols = matrix[0].len();
    
        let mut transposed = vec![vec![0.0; rows]; cols];
    
        for i in 0..rows {
            for j in 0..cols {
                transposed[j][i] = matrix[i][j];
            }
        }
    
        transposed
    }
    
    //ReLU function
    //activation function for the hidden layers
    //returns the input if it is positive, otherwise returns 0
    //this function is used to introduce non-linearity to the model
    pub fn ReLU(&self, z: Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        z.into_iter()
            .map(|row| row.into_iter().map(|x| x.max(0.0)).collect())
            .collect()
    }

    //Multiply matrix function
    //multiplies two matrices
    fn multiply_matrix(&self, weights: &Vec<Vec<f32>>, inputs: &Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        let mut result = vec![vec![0.0; weights.len()]; inputs.len()];
        for i in 0..inputs.len() {
            for j in 0..weights.len() {
                let mut sum = 0.0;
                for k in 0..weights[0].len() {
                    sum += weights[j][k] * inputs[i][k];
                }
                result[i][j] = sum;
            }
        }
        result
    }

    //Add bias function
    //adds the bias to the matrix
    fn ddd_matrix(&self, mat: Vec<Vec<f32>>, bias: &Vec<f32>) -> Vec<Vec<f32>> {
        let mut result = mat.clone();
        for i in 0..result.len() {
            for j in 0..result[i].len() {
                result[i][j] += bias[j];
            }
        }
        result
    }
    //Softmax function
    //converts the output of the last layer to probabilities
    pub fn softmax(&self, z: &Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        z.iter()
            .map(|row| {
                let max_val = row.iter().cloned().fold(f32::MIN, f32::max);
                let exp_row: Vec<f32> = row.iter().map(|&x| (x - max_val).exp()).collect();
                let sum_exp = exp_row.iter().sum::<f32>();
                exp_row.into_iter().map(|x| x / sum_exp).collect()
            })
            .collect()
    }

    pub fn print_params(&self){
        println!("Weights: {:?}", self.w);
        println!("Biases: {:?}", self.b);
    }

    pub fn elementwise_multiply(
        &self,
        a: &Vec<Vec<f32>>,
        b: &Vec<Vec<f32>>
    ) -> Vec<Vec<f32>> {
        let rows = a.len();
        let cols = a[0].len();
        let mut result = vec![vec![0.0; cols]; rows];
        for i in 0..rows {
            for j in 0..cols {
                result[i][j] = a[i][j] * b[i][j];
            }
        }
        result
    }

    pub fn sum_rows(&self, matrix: &Vec<Vec<f32>>, scale: f32) -> Vec<f32> {
        let rows = matrix.len();
        let cols = matrix[0].len();
        let mut result = vec![0.0; rows];
        for i in 0..rows {
            let mut sum = 0.0;
            for j in 0..cols {
                sum += matrix[i][j];
            }
            result[i] = sum * scale;
        }
        result
    }

    pub fn scale_matrix(&self, matrix: Vec<Vec<f32>>, scalar: f32) -> Vec<Vec<f32>> {
        let mut result = matrix.clone();
        for row in result.iter_mut() {
            for val in row.iter_mut() {
                *val *= scalar;
            }
        }
        result
    }

    pub fn relu_deriv(&self, z: &Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        z.iter()
            .map(|row| row.iter().map(|&x| if x > 0.0 { 1.0 } else { 0.0 }).collect())
            .collect()
    }

    pub fn subtract_matrix(&self, a: &Vec<Vec<f32>>, b: &Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        let rows = a.len();
        let cols = a[0].len();
        let mut result = vec![vec![0.0; cols]; rows];
        for i in 0..rows {
            for j in 0..cols {
                result[i][j] = a[i][j] - b[i][j];
            }
        }
        result
    }

    pub fn multiply_scalar(&self, a: &Vec<Vec<f32>>, scalar: f32) -> Vec<Vec<f32>> {
        let rows = a.len();
        let cols = a[0].len();
        let mut result = vec![vec![0.0; cols]; rows];
        for i in 0..rows {
            for j in 0..cols {
                result[i][j] = a[i][j] * scalar;
            }
        }
        result
    }

    pub fn multiply_scalar_vector(&self, a: &Vec<f32>, scalar: f32) -> Vec<f32> {
        let mut result = a.clone();
        for i in 0..a.len() {
            result[i] *= scalar;
        }
        result
    }

    pub fn subtract_vector(&self, a: &Vec<f32>, b: &Vec<f32>) -> Vec<f32> {
        let mut result = vec![0.0; a.len()];
        for i in 0..a.len() {
            result[i] = a[i] - b[i];
        }
        result
    }

    // Simple ReLU
    pub fn relu(&self, x: Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        x.into_iter()
            .map(|row| row.into_iter().map(|v| v.max(0.0)).collect())
            .collect()
    }


    // Simple cross-entropy loss
    pub fn compute_loss(&mut self, predictions: Vec<Vec<f32>>, labels: Vec<usize>) -> f32 {
        // Convert to one-hot
        let one_hot_labels = self.one_hot_encode(labels, predictions[0].len());
        let mut total_loss = 0.0;
        for (pred_row, label_row) in predictions.iter().zip(one_hot_labels.iter()) {
            for (&p, &l) in pred_row.iter().zip(label_row.iter()) {
                if l > 0.0 && p > 0.0 {
                    total_loss -= l * p.ln();
                }
            }
        }
        total_loss / (predictions.len() as f32)
    }

    // Predict class indices from final activations
    pub fn predict(&self, output: &Vec<Vec<f32>>) -> Vec<usize> {
        let mut preds = vec![];
        for row in output {
            let mut max_index = 0;
            let mut max_val = f32::MIN;
            for (j, &val) in row.iter().enumerate() {
                if val > max_val {
                    max_val = val;
                    max_index = j;
                }
            }
            preds.push(max_index);
        }
        preds
    }

    // Example training loop skeleton
    pub fn train(&mut self, x: Vec<Vec<f32>>, y: Vec<usize>, epochs: usize, alpha: f32) {
        for _ in 0..epochs {
            // forward_prop, backward_prop, update_params, etc.
            self.forward_propagation();
            self.backward_propagation(y.clone());
            self.update_params(alpha);
        }
    }
}