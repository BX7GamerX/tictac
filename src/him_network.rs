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