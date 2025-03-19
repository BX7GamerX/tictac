import numpy as np

class ActivationFunction:
    """Class for various activation functions and their derivatives"""
    
    @staticmethod
    def sigmoid(x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    @staticmethod
    def sigmoid_derivative(x):
        s = ActivationFunction.sigmoid(x)
        return s * (1 - s)
    
    @staticmethod
    def relu(x):
        return np.maximum(0, x)
    
    @staticmethod
    def relu_derivative(x):
        return np.where(x > 0, 1, 0)
    
    @staticmethod
    def tanh(x):
        return np.tanh(x)
    
    @staticmethod
    def tanh_derivative(x):
        return 1 - np.tanh(x) ** 2
    
    @staticmethod
    def softmax(x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    @staticmethod
    def cross_entropy_loss(y_pred, y_true):
        """Compute cross entropy loss for classification tasks"""
        # Add small epsilon to avoid log(0)
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -np.mean(y_true * np.log(y_pred))


class Layer:
    def __init__(self, input_size, output_size, activation='sigmoid'):
        self.weights = np.random.randn(input_size, output_size) * 0.01
        self.bias = np.zeros((1, output_size))
        
        if activation == 'sigmoid':
            self.activation = ActivationFunction.sigmoid
            self.activation_derivative = ActivationFunction.sigmoid_derivative
        elif activation == 'relu':
            self.activation = ActivationFunction.relu
            self.activation_derivative = ActivationFunction.relu_derivative
        elif activation == 'tanh':
            self.activation = ActivationFunction.tanh
            self.activation_derivative = ActivationFunction.tanh_derivative
        elif activation == 'softmax':
            self.activation = ActivationFunction.softmax
            self.activation_derivative = None  # Special handling for softmax with cross-entropy
        
        self.input = None
        self.z = None
        self.output = None
    
    def forward(self, input_data):
        self.input = input_data
        self.z = np.dot(input_data, self.weights) + self.bias
        self.output = self.activation(self.z)
        return self.output


class NeuralNetwork:
    def __init__(self, learning_rate=0.01, loss='mse'):
        self.layers = []
        self.learning_rate = learning_rate
        self.loss_type = loss
    
    def add_layer(self, input_size, output_size, activation='sigmoid'):
        self.layers.append(Layer(input_size, output_size, activation))
    
    def forward(self, X):
        output = X
        for layer in self.layers:
            output = layer.forward(output)
        return output
    
    def compute_loss(self, y_pred, y_true):
        if self.loss_type == 'mse':
            # Mean squared error
            return np.mean(np.square(y_true - y_pred))
        elif self.loss_type == 'cross_entropy':
            # Cross entropy loss
            return ActivationFunction.cross_entropy_loss(y_pred, y_true)
    
    def compute_loss_derivative(self, y_pred, y_true):
        if self.loss_type == 'mse':
            return -2 * (y_true - y_pred) / y_pred.shape[0]
        elif self.loss_type == 'cross_entropy':
            # For cross entropy with softmax, the gradient is just pred - true
            return y_pred - y_true
    
    def backward(self, X, y):
        m = y.shape[0]
        
        # Forward pass
        y_pred = self.forward(X)
        
        # Compute gradient of output layer
        dL_dy = self.compute_loss_derivative(y_pred, y)
        
        # Backpropagation
        dZ = None
        
        for i in reversed(range(len(self.layers))):
            layer = self.layers[i]
            
            if i == len(self.layers) - 1:  # Output layer
                if layer.activation == ActivationFunction.softmax:
                    # Special case for softmax + cross-entropy
                    dZ = y_pred - y
                else:
                    dZ = dL_dy * layer.activation_derivative(layer.z)
            else:  # Hidden layers
                next_layer = self.layers[i+1]  # Get actual next layer
                dA = np.dot(dZ, next_layer.weights.T)
                dZ = dA * layer.activation_derivative(layer.z)
            
            # Compute gradients
            dW = np.dot(layer.input.T, dZ) / m
            dB = np.sum(dZ, axis=0, keepdims=True) / m
            
            # Update parameters
            layer.weights -= self.learning_rate * dW
            layer.bias -= self.learning_rate * dB
    
    def train(self, X, y, epochs=1000, batch_size=32, verbose=True):
        m = X.shape[0]
        loss_history = []
        
        for epoch in range(epochs):
            # Mini-batch gradient descent
            indices = np.random.permutation(m)
            
            for i in range(0, m, batch_size):
                batch_indices = indices[i:min(i + batch_size, m)]
                X_batch = X[batch_indices]
                y_batch = y[batch_indices]
                
                # Forward and backward pass
                self.backward(X_batch, y_batch)
            
            # Compute loss for monitoring
            y_pred = self.forward(X)
            loss = self.compute_loss(y_pred, y)
            loss_history.append(loss)
            
            if verbose and epoch % 100 == 0:
                print(f"Epoch {epoch}, Loss: {loss:.4f}")
        
        return loss_history
    
    def predict(self, X):
        return self.forward(X)

