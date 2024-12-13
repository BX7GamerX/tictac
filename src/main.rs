mod output;
use output::position_to_index;
use output::Game;
use output::Table;
use output::Player;
fn main() {
    let mut tictac_game = output::Game::new();
    tictac_game.play();
}
