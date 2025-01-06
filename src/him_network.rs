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
        }
    }

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

    pub fn add_x1(&mut self, x1: Vec<f32>, index: usize) {
        if index < self.x1.len() {
            self.x1[index] = x1;
        }
    }

    pub fn forward_propagation(&mut self) {
        let z1 = self.ddd_matrix(self.multiply_matrix(&self.w1, &self.x1), &self.b1);
        let a1 = self.ReLU(z1);
        let z2 = self.ddd_matrix(self.multiply_matrix_81(&self.w2, &a1), &self.b2);
        let _a2 = self.softmax(z2);
    }

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

    fn multiply_matrix_81(&self, weights: &Vec<Vec<f32>>, inputs: &Vec<Vec<f32>>) -> Vec<Vec<f32>> {
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

    fn ddd_matrix(&self, mat: Vec<Vec<f32>>, bias: &Vec<f32>) -> Vec<Vec<f32>> {
        let mut result = mat.clone();
        for i in 0..result.len() {
            for j in 0..result[i].len() {
                result[i][j] += bias[j];
            }
        }
        result
    }

    fn softmax(&self, input: Vec<Vec<f32>>) -> Vec<Vec<f32>> {
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
}