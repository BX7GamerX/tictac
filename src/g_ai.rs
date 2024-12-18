/*mod g_class;
use g_class::NeuralNetwork;
use std::io;
use output::Player;

pub fn recommend_play(nn: &NeuralNetwork, player: &Player, table: &Table) -> i32 {
    let mut best_play = 0;
    let mut best_score = -1.0;
    for i in 0..9 {
        if table.is_empty(i) {
            let mut input = vec![0.0; 9];
            input[i] = 1.0;
            let (hidden, output) = nn.forward(&input);
            if output[0] > best_score {
                best_score = output[0];
                best_play = i;
            }
        }
    }
    best_play
}
*/