use rand::Rng;

pub struct HimNetwork{
    pub w1: [[f32; 9]; 81],
    pub w2: [[f32; 81]; 81],
    pub w3: [[f32; 81]; 81],
    pub w4: [[f32; 81]; 9],

    pub b1: [f32; 81],
    pub b2: [f32; 81],
    pub b3: [f32; 81],
    pub b4: [f32; 9],
}
impl HimNetwork {
    pub fn new() -> HimNetwork {
        HimNetwork {w1: [[0.0; 9]; 81], w2: [[0.0; 81]; 81], w3: [[0.0; 81]; 81], w4: [[0.0; 81]; 9],
                     b1: [0.0; 81], b2: [0.0; 81], b3: [0.0; 81], b4: [0.0; 9]}
    }
    pub fn init_params(&mut self){
        const CONNECTIONS_COUNT :i64 = 9;
        const NODES_COUNT :i64 = 81;
        //self.w1 = [[3.14159; CONNECTIONS_COUNT as usize]; NODES_COUNT as usize];// w1(81,9)
        //w1 (nodes{81}, connections{9})
        //w2 (nodes{81}, connections{81})
        //w3 (nodes{81}, connections{81})
        //w4 (nodes{9}, connections{81})
        //b1 (nodes{81})
        //b2 (nodes{81})
        //b3 (nodes{81})
        //b4 (nodes{9})
        // Initialize the weights and biases
        for nodes in 0 .. NODES_COUNT {
            self.w1[nodes as usize] = [rand::thread_rng().gen_range(0.0..1.0) - 0.5;CONNECTIONS_COUNT as usize];
            self.w2[nodes as usize] = [rand::thread_rng().gen_range(0.0..1.0) - 0.5;NODES_COUNT as usize];
            self.w3[nodes as usize] = [rand::thread_rng().gen_range(0.0..1.0) - 0.5;NODES_COUNT as usize];
            
            if nodes % 9 == 0 {
                self.w4[(nodes/9) as usize] = [rand::thread_rng().gen_range(0.0..1.0) - 0.5; NODES_COUNT as usize];
            }
        }
    }






























    pub fn forward_propagation (&mut self,moves_count: Vec <[i8;9]>) {
        //let mut z1 = self.w1 * 
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