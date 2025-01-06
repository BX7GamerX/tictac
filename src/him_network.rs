use core::num;

use rand::Rng;

pub struct HimNetwork {
    //  layer : connections : nodes
    pub w1: Vec<Vec<f32>>,
    pub w2: Vec<Vec<f32>>,
    pub w3: Vec<Vec<f32>>,
    pub w4: Vec<Vec<f32>>,
    
    pub x1: Vec<Vec<f32>>, // 10000 games

    pub b1: Vec<f32>,
    pub b2: Vec<f32>,
    pub b3: Vec<f32>,
    pub b4: Vec<f32>,

    pub z1: Vec<Vec<f32>>,
    pub a1: Vec<Vec<f32>>,
    pub z2: Vec<Vec<f32>>,
    pub a2: Vec<Vec<f32>>,
    pub z3: Vec<Vec<f32>>,
    pub a3: Vec<Vec<f32>>,
    pub z4: Vec<Vec<f32>>,
    pub a4: Vec<Vec<f32>>,
}

impl HimNetwork {
    pub fn new() -> HimNetwork {
        HimNetwork {
            w1: vec![vec![0.0; 9]; 81],
            w2: vec![vec![0.0; 81]; 81],
            w3: vec![vec![0.0; 81]; 81],
            w4: vec![vec![0.0; 81]; 9],
            b1: vec![0.0; 81],
            b2: vec![0.0; 81],
            b3: vec![0.0; 81],
            b4: vec![0.0; 9],
            x1: vec![vec![0.0; 9]; 10000],
            z1: vec![vec![0.0; 9]; 10000],
            a1: vec![vec![0.0; 9]; 10000],
            z2: vec![vec![0.0; 81]; 10000],
            a2: vec![vec![0.0; 81]; 10000],
            z3: vec![vec![0.0; 81]; 10000],
            a3: vec![vec![0.0; 81]; 10000],
            z4: vec![vec![0.0; 9]; 10000],
            a4: vec![vec![0.0; 9]; 10000],
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
        // Initialize the weights and biases
        for nodes in 0..NODES_COUNT {
            self.w1[nodes] = vec![rand::thread_rng().gen_range(0.0..1.0) - 0.5; CONNECTIONS_COUNT];
            self.w2[nodes] = vec![rand::thread_rng().gen_range(0.0..1.0) - 0.5; NODES_COUNT];
            self.w3[nodes] = vec![rand::thread_rng().gen_range(0.0..1.0) - 0.5; NODES_COUNT];
            self.b1[nodes] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            self.b2[nodes] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            self.b3[nodes] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;

            if nodes % 9 == 0 {
                self.w4[nodes / 9] = vec![rand::thread_rng().gen_range(0.0..1.0) - 0.5; NODES_COUNT];
                self.b4[nodes / 9] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            }
        }
    }

    //Forward propagation
    pub fn forward_propagation(&mut self) {
        //First layer
        self.z1 = self.ddd_matrix(self.multiply_matrix(&self.w1, &self.x1), &self.b1);
        self.a1 = self.ReLU(self.z1.clone());
        //Second layer
        self.z2 = self.ddd_matrix(self.multiply_matrix(&self.w2, &self.a1), &self.b2);
        self.a2 = self.ReLU(self.z2.clone());
        //Third layer
        self.z3 = self.ddd_matrix(self.multiply_matrix(&self.w3, &self.a2), &self.b3);
        self.a3 = self.ReLU(self.z3.clone());
        //Fourth layer
        self.z4 = self.ddd_matrix(self.multiply_matrix(&self.w4, &self.a3), &self.b4);
        self.a4 = self.softmax(&self.z4);
        
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
        let mut dZ4 = vec![vec![0.0; self.a4[0].len()]; self.a4.len()];
        for i in 0..self.a4.len() {
            for j in 0..self.a4[i].len() {
                dZ4[i][j] = self.a4[i][j] - one_hot_y[i][j];
            }
        }
        let a3_t = self.transpose(self.a3.clone());
        let dZ4_a3_t = self.multiply_matrix(&dZ4, &a3_t);
        let dW4: Vec<Vec<f32>> = dZ4_a3_t
            .iter()
            .map(|row| row.iter().map(|val| val * reciprocal_m).collect())
            .collect();
        let db4 = self.sum_rows(&dZ4, reciprocal_m);

        // Gradient for third layer
        let w4_t = self.transpose(self.w4.clone());
        let dA3 = self.multiply_matrix(&w4_t, &dZ4);
        let dZ3 = self.elementwise_multiply(&dA3, &self.relu_deriv(&self.z3));
        let a2_t = self.transpose(self.a2.clone());
        let dZ3_a2_t = self.multiply_matrix(&dZ3, &a2_t);
        let dW3 = self.scale_matrix(dZ3_a2_t, reciprocal_m);
        let db3 = self.sum_rows(&dZ3, reciprocal_m);

        // Gradient for second layer
        let w3_t = self.transpose(self.w3.clone());
        let dA2 = self.multiply_matrix(&w3_t, &dZ3);
        let dZ2 = self.elementwise_multiply(&dA2, &self.relu_deriv(&self.z2));
        let a1_t = self.transpose(self.a1.clone());
        let dZ2_a1_t = self.multiply_matrix(&dZ2, &a1_t);
        let dW2 = self.scale_matrix(dZ2_a1_t, reciprocal_m);
        let db2 = self.sum_rows(&dZ2, reciprocal_m);

        // Gradient for first layer
        let w2_t = self.transpose(self.w2.clone());
        let dA1 = self.multiply_matrix(&w2_t, &dZ2);
        let dZ1 = self.elementwise_multiply(&dA1, &self.relu_deriv(&self.z1));
        let x_t = self.transpose(self.x1.clone());
        let dZ1_x_t = self.multiply_matrix(&dZ1, &x_t);
        let dW1 = self.scale_matrix(dZ1_x_t, reciprocal_m);
        let db1 = self.sum_rows(&dZ1, reciprocal_m);

        // ...apply updates or store gradients...
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
    fn ReLU(&self, input: Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        let mut output = input.clone();
        for i in 0..output.len() {
            for j in 0..output[i].len() {
                if output[i][j] < 0.0 {
                    output[i][j] = 0.0;
                }
            }
        }
        output
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
    fn softmax(&self, input: &Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        let mut output = vec![vec![0.0; input[0].len()]; input.len()];
        for i in 0..input.len() {
            let sum: f32 = input[i].iter().map(|x| x.exp()).sum();
            for j in 0..input[i].len() {
                output[i][j] = input[i][j].exp() / sum;
            }
        }
        output
    }

    pub fn print_params(&self){
        println!("w1: {:?}", self.w1);
        println!("w2: {:?}", self.w2);
        println!("w3: {:?}", self.w3);
        println!("w4: {:?}", self.w4);
        println!("b1: {:?}", self.b1);
        println!("b2: {:?}", self.b2);
        println!("b3: {:?}", self.b3);
        println!("b4: {:?}", self.b4);
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
        let rows = z.len();
        let cols = z[0].len();
        let mut result = vec![vec![0.0; cols]; rows];
        for i in 0..rows {
            for j in 0..cols {
                if z[i][j] > 0.0 {
                    result[i][j] = 1.0;
                }
            }
        }
        result
    }

    
    
}