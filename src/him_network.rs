use rand::Rng;
use std::collections::HashMap;
use std::io;

pub struct HimNode{
    pub value: i32,
    pub index: i8,

}
impl HimNode {
    pub fn new(position:i8,data: i8) -> HimNode {
        HimNode {
            index: position,
            value: data as i32,
        }
    }
}

pub struct HimNetwork{
    pub input_nodes: HashMap<i32, HimNode>,
    pub output_nodes: HashMap<i32, HimNode>,
    pub w1: [[f32; 9]; 10],
    pub w2: [[f32; 10]; 10],
    pub b1: [f32; 10],
    pub b2: [f32; 10],
}
impl HimNetwork {
    pub fn new() -> HimNetwork {
        HimNetwork { input_nodes: HashMap::new(), output_nodes: HashMap::new() ,
            w1: [[0.0; 9]; 10], w2: [[0.0; 10]; 10], b1: [0.0; 10], b2: [0.0; 10] }
    }
    pub fn init_params(&mut self){
        const INPUT_LAYER_SIZE :i64 = 9;
        const HIDDEN_LAYER_SIZE :i64 = 10;
        self.w1 = [[3.14159; 9]; 10] ;// W1 (10,9) => 10 hidden nodes, 9 input nodes
        self.w2 = [[3.14159; 10]; 10];// W2 (10,10) ==> 10 hidden nodes, 10 hidden nodes
        self.b1 = [3.14159; 10];// B1 (10,1) ==> 10 hidden nodes
        self.b2 = [3.14159; 10];// B2 (10,1) ==> 10 hidden nodes
        // Initialize the weights and biases
        for layers in 0 .. HIDDEN_LAYER_SIZE {
            for inputs in 0 .. INPUT_LAYER_SIZE {
                self.w1[layers as usize][inputs as usize] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            }
            for inputs in 0.. HIDDEN_LAYER_SIZE {
                self.w2[layers as usize][inputs as usize] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            }// Initialize the biases
            self.b1[layers as usize] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            self.b2[layers as usize] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
        }
    }
    pub fn forward_propagation (&mut self,moves_count: Vec <[i8;9]>) {
        //let mut z1 = self.w1 * 
    }






























    pub fn print_params(&self){
        for layers in 0..10 {
            for inputs in 0..9 {
                println!("w1[{}][{}] = {}", layers, inputs, self.w1[layers as usize][inputs as usize]);
            }
            for inputs in 0..10 {
                println!("w2[{}][{}] = {}", layers, inputs, self.w2[layers as usize][inputs as usize]);
            }
            println!("b1[{}] = {}", layers, self.b1[layers as usize]);
            println!("b2[{}] = {}", layers, self.b2[layers as usize]);
        }
    }
    pub fn add_input_node(&mut self, input_list: [i8;9]) {
        let mut index = 0;
        for data in input_list.iter() {
            let node = HimNode::new(index,*data);
            self.input_nodes.insert(index as i32, node);
            index += 1;
        }
    }
    pub fn print_input_nodes(&self) {
        for (key, value) in &self.input_nodes {
            println!("{}: {}", key, value.value);
        }
    }

}