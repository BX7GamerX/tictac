
mod input;
mod output;
mod g_class;
mod g_ai;
mod him_network;

fn test_game(){
    let player_type = String::from("ai_Vs_ai");
    let mut cycles_count = 0;
    let cycles_limit = 2;//output::get_int("Enter the number of cycles to play: ");
    loop {
        let mut tictac_game = output::Game::new(player_type.clone());
        tictac_game.play();
        cycles_count += 1;
        if cycles_count >= cycles_limit {
            break;
        }
    }
}
fn main() {
    test_game();
    let mut game_data = input::GamesData::new(String::from("table.csv"));
    game_data.read_data();
    game_data.print_game(4);

}

