mod output;
mod g_class;
mod g_ai;
use output::position_to_index;
use output::Game;
use output::Table;
use output::Player;
fn main() {
    loop {
        let mut tictac_game = output::Game::new();
        tictac_game.play();
        
    }
}

