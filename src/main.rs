mod output;
use output::position_to_index;
use output::Table;
use output::Player;
fn main() {
    let mut tictac_board = Table::new();
    tictac_board.init();
    let mut player1 = Player::new("Player 1".to_string(), 'X');
    loop {
    let mut input = output::get_int("");
    let mut count = 0;
    player1.play(&mut tictac_board, input);
    if tictac_board.check_full() {
        println!("It's a draw!");
        break;
    }
    count += 1;
    }
}
