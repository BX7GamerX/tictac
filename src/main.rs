
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
    test_game();
    let mut game_data = input::GamesData::new(String::from("table.csv"));
    game_data.read_data();
    let mut network = him_network::HimNetwork::new();
    let mut game_one = game_data.get_game(0);
    game_one.print_game();
    let round_one = game_one.get_round_State(7);
    network.add_input_node(round_one);
    //game_data.print_game(4);
    network.print_input_nodes();
}

fn main() {
    let test_network = him_network::HimNetwork::new();
    let (w1,w2,b1,b2) = test_network.init_params();
    println!("{:?}", w1[0]);
}

