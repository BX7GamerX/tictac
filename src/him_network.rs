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
    pub nodes: HashMap<i32, HimNode>,
}
impl HimNetwork {
    pub fn new(value_list_in: [i8;9]) -> HimNetwork {
        let mut nodes = HashMap::new();
        let mut count = 0;
        for value in value_list_in.iter(){
            let node = HimNode::new(count, *value);
            nodes.insert(node.value, node);
            count += 1;
        }
        HimNetwork { nodes }
    }
}