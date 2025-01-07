
use him_network::HimNetwork;


mod input;
mod output;
mod g_class;
mod g_ai;
mod him_network;

fn test_game(){
    let player_type = String::from("ai_Vs_ai");
    let mut cycles_count = 0;
    let cycles_limit = 200;//output::get_int("Enter the number of cycles to play: ");
    loop {
        let mut tictac_game = output::Game::new(player_type.clone());
        tictac_game.play();
        cycles_count += 1;
        if cycles_count >= cycles_limit {
            break;
        }
    }
}
fn test_reading () {
    //test_game();
    let mut game_data = input::GamesData::new(String::from("table.csv"));
    game_data.read_data();
    let network = him_network::HimNetwork::new();
    let game_one = game_data.get_game(0);
    //game_one.print_game();
    let data = game_one.state_of_cells_list;
    println!("Data: {:?}", data);

} 


use rand::Rng;

fn main() {
    let mut him_net = HimNetwork::new(); // Initialize the network with 5 layers
    him_net.init_params(); // Initialize weights and biases

    // Generate test input data
    let mut rng = rand::thread_rng();
    for i in 0..10000 {
        for j in 0..9 {
            him_net.x1[i][j] = rng.gen_range(0.0..1.0); // Random values between 0 and 1
        }
    }

    // Generate target labels (random integers between 0 and 8)
    let y: Vec<usize> = (0..10000).map(|_| rng.gen_range(0..9)).collect();

    // Perform forward propagation
    him_net.forward_propagation();
    println!("Forward propagation completed.");

    // Perform backward propagation with the generated labels
    him_net.backward_propagation(y);
    println!("Backward propagation completed.");

    // Optionally, print a summary of weights, biases, and output
    println!("Sample weights (Layer 1): {:?}", &him_net.w[1][..5]);
    println!("Sample biases (Layer 1): {:?}", &him_net.b[1][..5]);
    println!("Sample output (Layer 4 activations): {:?}", &him_net.a[4][..5]);
}
