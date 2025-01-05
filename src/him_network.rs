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
}
impl HimNetwork {
    pub fn new() -> HimNetwork {
        HimNetwork { input_nodes: HashMap::new(), output_nodes: HashMap::new() }
    }
    pub fn init_params(self)-> ( [[f32; 9]; 10], [[f32; 10]; 10], [f32; 10], [f32; 10]) {
        const INPUT_LAYER_SIZE :i64 = 9;
        const HIDDEN_LAYER_SIZE :i64 = 10;
        let mut w1 :[[f32; INPUT_LAYER_SIZE as usize]; HIDDEN_LAYER_SIZE as usize] = [[3.14159; 9]; 10] ;
        let mut w2 :[[f32; HIDDEN_LAYER_SIZE as usize]; HIDDEN_LAYER_SIZE as usize] = [[3.14159; 10]; 10];
        let mut b1 :[f32; HIDDEN_LAYER_SIZE as usize] = [3.14159; 10];
        let mut b2 :[f32; HIDDEN_LAYER_SIZE as usize] = [3.14159; 10];

        for layers in 0 .. HIDDEN_LAYER_SIZE {
            for inputs in 0 .. INPUT_LAYER_SIZE {
                w1[layers as usize][inputs as usize] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            }
            for inputs in 0.. HIDDEN_LAYER_SIZE {
                w2[layers as usize][inputs as usize] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            }
            b1[layers as usize] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
            b2[layers as usize] = rand::thread_rng().gen_range(0.0..1.0) - 0.5;
        }
        (w1,w2,b1,b2)

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