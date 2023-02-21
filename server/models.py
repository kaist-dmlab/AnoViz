import numpy as np

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import Model, Input, layers

#####################################BASIC#####################################
# CNN-AE
def CNN_AE(X_train):
    Conv1D = layers.Conv1D
    Conv1DT = layers.Conv1DTranspose
    Dropout = layers.Dropout

    model = keras.Sequential(
        [
            layers.InputLayer(input_shape=(X_train.shape[1], X_train.shape[2])),
            Conv1D(32, 7, padding='same', strides=2, activation='relu'),
            Dropout(0.4),
            Conv1D(16, 7, padding='same', strides=2, activation='relu'),
            Conv1DT(16, 7, padding='same', strides=2, activation='relu'),
            Dropout(0.4),
            Conv1DT(32, 7, padding='same', strides=2, activation='relu'),
            Conv1DT(1, 7, padding='same')
        ]
    )
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    model.fit(X_train, X_train, epochs=50, batch_size=128, validation_split=0.3, verbose=0, callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)])    
    return model

# GRU-AE
def GRU_AE(X_train):
    GRU = layers.GRU
    Dropout = layers.Dropout
    model = keras.Sequential(
        [
            layers.InputLayer(input_shape=(X_train.shape[1], X_train.shape[2])),
            GRU(64, return_sequences=True),
            Dropout(0.4),
            GRU(32),
            layers.RepeatVector(X_train.shape[1]),
            GRU(32, return_sequences=True),
            Dropout(0.4),
            GRU(64),
            layers.Dense(X_train.shape[1] *  X_train.shape[2]),
            layers.Reshape([X_train.shape[1], X_train.shape[2]])
        ]
    )
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    history = model.fit(X_train, X_train, epochs=50, batch_size=128, validation_split=0.3, verbose=0, callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)])
    return model

# BiGRU-AE
def BiGRU_AE(X_train):
    Bi = layers.Bidirectional
    GRU = layers.GRU
    model = keras.Sequential(
        [
            layers.InputLayer(input_shape=(X_train.shape[1], X_train.shape[2])),
            Bi(GRU(128, return_sequences=True)),
            layers.Dropout(rate=0.2),
            Bi(GRU(64)),
            layers.RepeatVector(X_train.shape[1]),
            Bi(GRU(64, return_sequences=True)),
            layers.Dropout(rate=0.2),
            Bi(GRU(128)),
            layers.Dense(X_train.shape[1] *  X_train.shape[2]),
            layers.Reshape([X_train.shape[1], X_train.shape[2]])
        ]
    )
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    history = model.fit(X_train, X_train, epochs=50, batch_size=64, validation_split=0.3, verbose=0, callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)])
    return model

# LSTM-AE
def LSTM_AE(X_train):
    LSTM = layers.LSTM
    Dropout = layers.Dropout
    model = keras.Sequential(
        [
            layers.InputLayer(input_shape=(X_train.shape[1], X_train.shape[2])),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            layers.RepeatVector(X_train.shape[1]),
            LSTM(32, return_sequences=True),
            Dropout(0.2),
            LSTM(64),
            layers.Dense(X_train.shape[1] *  X_train.shape[2]),
            layers.Reshape([X_train.shape[1], X_train.shape[2]])
        ]
    )
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    history = model.fit(X_train, X_train, epochs=50, batch_size=128, validation_split=0.3, verbose=0, callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)])    
    return model

####################################TEMPORAL###################################
# CNN-AE
def CNN_AE_Temporal(X_train_ax, X_train):
    RepeatVector = layers.RepeatVector
    Reshape = layers.Reshape
    Conv1D = layers.Conv1D
    Conv1DT = layers.Conv1DTranspose
    Dropout = layers.Dropout
    Dense = layers.Dense
    
    temporal_input = keras.Input(shape=(X_train_ax.shape[1], X_train_ax.shape[2]), name='temporal_input')
    ts_input = keras.Input(shape=(X_train.shape[1], X_train.shape[2]), name='ts_input')
    inputs = [temporal_input, ts_input]
    
    ## Temporal information embedding
    x = Dense(32, activation='relu')(temporal_input)
    x = Dense(4, activation='relu')(x)
    x = layers.Flatten()(x)
    x = Dense(X_train.shape[1] * X_train.shape[2])(x)
    temporal_output = Reshape((X_train.shape[1], X_train.shape[2]))(x)
    
    ## Time-series autoencoder
    concat = layers.concatenate([ts_input, temporal_output], axis=-1)
    x = Conv1D(32, 7, padding='same', strides=2, activation='relu')(concat)
    x = Dropout(0.2)(x)
    x = Conv1D(16, 7, padding='same', strides=2, activation='relu')(x)
    x = Conv1DT(16, 7, padding='same', strides=2, activation='relu')(x)
    x = Dropout(0.2)(x)
    x = Conv1DT(32, 7, padding='same', strides=2, activation='relu')(x)
    ts_output = Conv1DT(1, 7, padding='same')(x)
    
    model = keras.Model(inputs=inputs, outputs=ts_output)
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    model.fit([X_train_ax, X_train], X_train, epochs=50, batch_size=128, validation_split=0.3, verbose=0, callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)])    
    return model

# GRU-AE
def GRU_AE_Temporal(X_train_ax, X_train):
    RepeatVector = layers.RepeatVector
    Reshape = layers.Reshape
    GRU = layers.GRU
    Dense = layers.Dense
    
    temporal_input = keras.Input(shape=(X_train_ax.shape[1], X_train_ax.shape[2]), name='temporal_input')
    ts_input = keras.Input(shape=(X_train.shape[1], X_train.shape[2]), name='ts_input')
    inputs = [temporal_input, ts_input]
    
    ## Temporal information embedding
    x = Dense(32, activation='relu')(temporal_input)
    x = Dense(4, activation='relu')(x)
    x = layers.Flatten()(x)
    x = Dense(X_train.shape[1] * X_train.shape[2])(x)
    temporal_output = Reshape((X_train.shape[1], X_train.shape[2]))(x)
    
    ## Time-series autoencoder
    concat = layers.concatenate([ts_input, temporal_output], axis=-1)
    x = GRU(64, return_sequences=True)(concat)
    x = GRU(32)(x)
    x = layers.RepeatVector(X_train.shape[1])(x)
    x = GRU(32, return_sequences=True)(x)
    x = GRU(64)(x)
    x = Dense(X_train.shape[1] *  X_train.shape[2])(x)
    ts_output = Reshape([X_train.shape[1], X_train.shape[2]])(x)
    
    model = keras.Model(inputs=inputs, outputs=ts_output)
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    model.fit([X_train_ax, X_train], X_train, epochs=50, batch_size=128, validation_split=0.3, verbose=0, callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)])    
    return model

# BiGRU-AE
def BiGRU_AE_Temporal(X_train_ax, X_train):
    RepeatVector = layers.RepeatVector
    Reshape = layers.Reshape
    Dense = layers.Dense
    Bi = layers.Bidirectional
    GRU = layers.GRU
    
    temporal_input = keras.Input(shape=(X_train_ax.shape[1], X_train_ax.shape[2]), name='temporal_input')
    ts_input = keras.Input(shape=(X_train.shape[1], X_train.shape[2]), name='ts_input')
    inputs = [temporal_input, ts_input]
    
    ## Temporal information embedding
    x = Dense(32, activation='relu')(temporal_input)
    x = Dense(4, activation='relu')(x)
    x = layers.Flatten()(x)
    x = Dense(X_train.shape[1] * X_train.shape[2])(x)
    temporal_output = Reshape((X_train.shape[1], X_train.shape[2]))(x)
    
    ## Time-series autoencoder
    concat = layers.concatenate([ts_input, temporal_output], axis=-1)
    x = Bi(GRU(128, return_sequences=True))(concat)
    x = layers.Dropout(rate=0.2)(x)
    x = Bi(GRU(64))(x)
    x = layers.RepeatVector(X_train.shape[1])(x)
    x = Bi(GRU(64, return_sequences=True))(x)
    x = layers.Dropout(rate=0.2)(x)
    x = Bi(GRU(128))(x)
    x = layers.Dense(X_train.shape[1] *  X_train.shape[2])(x)
    ts_output = layers.Reshape([X_train.shape[1], X_train.shape[2]])(x)
    
    model = keras.Model(inputs=inputs, outputs=ts_output)
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    model.fit([X_train_ax, X_train], X_train, epochs=50, batch_size=128, validation_split=0.3, verbose=0, callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)])    
    return model

# LSTM-AE
def LSTM_AE_Temporal(X_train_ax, X_train):
    RepeatVector = layers.RepeatVector
    Reshape = layers.Reshape
    Dense = layers.Dense
    LSTM = layers.LSTM
    
    temporal_input = keras.Input(shape=(X_train_ax.shape[1], X_train_ax.shape[2]), name='temporal_input')
    ts_input = keras.Input(shape=(X_train.shape[1], X_train.shape[2]), name='ts_input')
    inputs = [temporal_input, ts_input]
    
    ## Temporal information embedding
    x = Dense(32, activation='relu')(temporal_input)
    x = Dense(4, activation='relu')(x)
    x = layers.Flatten()(x)
    x = Dense(X_train.shape[1] * X_train.shape[2])(x)
    temporal_output = Reshape((X_train.shape[1], X_train.shape[2]))(x)
    
    ## Time-series autoencoder
    concat = layers.concatenate([ts_input, temporal_output], axis=-1)
    x = LSTM(64, return_sequences=True)(concat)
    x = LSTM(32)(x)
    x = layers.RepeatVector(X_train.shape[1])(x)
    x = LSTM(32, return_sequences=True)(x)
    x = LSTM(64)(x)
    x = layers.Dense(X_train.shape[1] *  X_train.shape[2])(x)
    ts_output = layers.Reshape([X_train.shape[1], X_train.shape[2]])(x)
    
    model = keras.Model(inputs=inputs, outputs=ts_output)
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    model.fit([X_train_ax, X_train], X_train, epochs=50, batch_size=128, validation_split=0.3, verbose=0, callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)])    
    return model

class Sampling(layers.Layer):
    """Uses (z_mean, z_log_var) to sample z, the vector encoding a digit."""

    def call(self, inputs):
        z_mean, z_log_var = inputs
        batch = tf.shape(z_mean)[0]
        dim = tf.shape(z_mean)[1]
        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon

class VAE(keras.Model):
    def __init__(self, encoder, decoder, **kwargs):
        super(VAE, self).__init__(**kwargs)
        self.encoder = encoder
        self.decoder = decoder
        self.total_loss_tracker = keras.metrics.Mean(name="total_loss")
        self.reconstruction_loss_tracker = keras.metrics.Mean(
            name="reconstruction_loss"
        )
        self.kl_loss_tracker = keras.metrics.Mean(name="kl_loss")

    @property
    def metrics(self):
        return [
            self.total_loss_tracker,
            self.reconstruction_loss_tracker,
            self.kl_loss_tracker,
        ]

    def train_step(self, data):
        with tf.GradientTape() as tape:
            z_mean, z_log_var, z = self.encoder(data)
            reconstruction = self.decoder(z)
            reconstruction_loss = tf.reduce_mean(
                tf.reduce_sum(
                    keras.losses.binary_crossentropy(data[0][1], reconstruction), axis=1
                )
            )
            kl_loss = -0.5 * (1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var))
            kl_loss = tf.reduce_mean(tf.reduce_sum(kl_loss, axis=1))
            total_loss = reconstruction_loss + kl_loss
        grads = tape.gradient(total_loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(grads, self.trainable_weights))
        self.total_loss_tracker.update_state(total_loss)
        self.reconstruction_loss_tracker.update_state(reconstruction_loss)
        self.kl_loss_tracker.update_state(kl_loss)
        return {
            "loss": self.total_loss_tracker.result(),
            "reconstruction_loss": self.reconstruction_loss_tracker.result(),
            "kl_loss": self.kl_loss_tracker.result(),
        }

# CNN_VAE
def CNN_VAE_Temporal(X_train_ax, X_train):
    latent_dim = 16

    temporal_input = keras.Input(shape=(X_train_ax.shape[1], X_train_ax.shape[2]), name='temporal_input')
    encoder_inputs = keras.Input(shape=(X_train.shape[1], X_train.shape[2]), name ='ts_input')
    inputs = [temporal_input, encoder_inputs]
    
    ## Temporal information embedding
    x = layers.Dense(32, activation='relu')(temporal_input)
    x = layers.Dense(4, activation='relu')(x)
    x = layers.Flatten()(x)
    x = layers.Dense(X_train.shape[1] * X_train.shape[2])(x)
    temporal_output = layers.Reshape((X_train.shape[1], X_train.shape[2]))(x)
    
    ## Time-series encoder
    concat = layers.concatenate([encoder_inputs, temporal_output], axis=-1)
    x = layers.Conv1D(32, 3, activation="relu", strides=2, padding="same")(concat)
    x = layers.Conv1D(64, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Flatten()(x)
    x = layers.Dense(128, activation="relu")(x)
    z_mean = layers.Dense(latent_dim, name="z_mean")(x)
    z_log_var = layers.Dense(latent_dim, name="z_log_var")(x)
    z = Sampling()([z_mean, z_log_var])
    encoder = keras.Model(inputs, [z_mean, z_log_var, z], name="encoder")
    
    latent_inputs = keras.Input(shape=(latent_dim,))
    x = layers.Dense(32* 64, activation="relu")(latent_inputs)
    x = layers.Reshape((32, 64))(x)
    x = layers.Conv1DTranspose(64, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Conv1DTranspose(32, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Flatten()(x)
    x = layers.Dense(X_train.shape[1] * X_train.shape[2])(x)
    decoder_outputs = layers.Reshape([X_train.shape[1], X_train.shape[2]])(x)
    decoder = keras.Model(latent_inputs, decoder_outputs, name="decoder")
    
    model = VAE(encoder, decoder)
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001))
    history = model.fit([X_train_ax, X_train], epochs=50, batch_size=128, verbose=0)
    return model

# GRU_VAE
def GRU_VAE_Temporal(X_train_ax, X_train):
    latent_dim = 16
    
    temporal_input = keras.Input(shape=(X_train_ax.shape[1], X_train_ax.shape[2]), name='temporal_input')
    encoder_inputs = keras.Input(shape=(X_train.shape[1], X_train.shape[2]), name ='ts_input')
    inputs = [temporal_input, encoder_inputs]

    ## Temporal information embedding
    x = layers.Dense(32, activation='relu')(temporal_input)
    x = layers.Dense(4, activation='relu')(x)
    x = layers.Flatten()(x)
    x = layers.Dense(X_train.shape[1] * X_train.shape[2])(x)
    temporal_output = layers.Reshape((X_train.shape[1], X_train.shape[2]))(x)
    
    ## Time-series encoder
    concat = layers.concatenate([encoder_inputs, temporal_output], axis=-1)    
    x = layers.GRU(64, return_sequences=True)(concat)
    x = layers.GRU(32)(x)
    z_mean = layers.Dense(latent_dim, name="z_mean")(x)
    z_log_var = layers.Dense(latent_dim, name="z_log_var")(x)
    z = Sampling()([z_mean, z_log_var])
    encoder = keras.Model(inputs, [z_mean, z_log_var, z], name="encoder")

    latent_inputs = keras.Input(shape=(latent_dim,))
    x = layers.RepeatVector(X_train.shape[1])(latent_inputs)
    x = layers.GRU(32, return_sequences=True)(x)
    x = layers.GRU(64)(x)
    x = layers.Dense(X_train.shape[1] *  X_train.shape[2])(x)
    decoder_outputs = layers.Reshape([X_train.shape[1], X_train.shape[2]])(x)
    decoder = keras.Model(latent_inputs, decoder_outputs, name="decoder")

    model = VAE(encoder, decoder)
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001))
    history = model.fit([X_train_ax, X_train], epochs=50, batch_size=128, verbose=0)
    return model

# CNN-GAN
def train_gan(temporal, gan, dataset_aux, dataset, batch_size, codings_size, dim=1, n_epochs=50):
    generator, discriminator = gan.layers
    for epoch in range(n_epochs):
        for X_batch, X_batch_aux in zip(dataset, dataset_aux):
            X_batch = tf.cast(X_batch, tf.float32)
            
            # phase 1 - training the discriminator
            noise = tf.random.normal(shape=[batch_size, codings_size, dim])
            temporal_info = temporal(X_batch_aux)
            generated_images = generator(noise)
            
            X_fake_and_real = tf.concat([generated_images, X_batch], axis=0)
            X_fake_and_real_temporal = tf.concat([X_fake_and_real, temporal_info], axis=0)
            
            y1 = tf.constant([[0.]] * batch_size + [[1.]] * batch_size + [[0.]] * batch_size)
            discriminator.trainable = True
            discriminator.train_on_batch(X_fake_and_real_temporal, y1)
            
            # phase 2 - training the generator
            noise = tf.random.normal(shape=[batch_size, codings_size, dim])
            y2 = tf.constant([[1.]] * batch_size)
            discriminator.trainable = False
            gan.train_on_batch(noise, y2)     
            
def get_gan(x_train_ax, x_train):    
    temporal_input = keras.Input(shape=(x_train_ax.shape[1], x_train_ax.shape[2]), name='temporal_input')
    ts_inputs = keras.Input(shape=(x_train.shape[1], x_train.shape[2]), name ='ts_input')

    ## Temporal information embedding
    x = layers.Dense(32, activation='relu')(temporal_input)
    x = layers.Dense(4, activation='relu')(x)
    x = layers.Flatten()(x)
    x = layers.Dense(x_train.shape[1] * x_train.shape[2])(x)
    temporal_output = layers.Reshape((x_train.shape[1], x_train.shape[2]))(x)
    temporal = keras.Model(temporal_input, temporal_output, name='temporal')

    ## Time-series GAN
    x = keras.layers.Conv1D(128, kernel_size=3, padding='SAME', activation=keras.layers.LeakyReLU(0.2))(ts_inputs)
    x = layers.InputLayer(input_shape=(x_train.shape[1], x_train.shape[2]))(x)
    x = keras.layers.Conv1D(128, kernel_size=3, padding='SAME', activation=keras.layers.LeakyReLU(0.2))(x)
    x = keras.layers.MaxPool1D(3, padding='SAME')(x)
    x = keras.layers.Conv1D(64, kernel_size=3, padding='SAME', activation=keras.layers.LeakyReLU(0.2))(x)
    x = keras.layers.MaxPool1D(3, padding='SAME')(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Conv1DTranspose(64, kernel_size=5, strides=2, padding="SAME", activation="selu")(x)
    x = keras.layers.BatchNormalization()(x)
    x = layers.Flatten()(x)
    x = layers.Dense(x_train.shape[1] * x_train.shape[2])(x)
    generator_output = layers.Reshape([x_train.shape[1], x_train.shape[2]])(x)
    generator = keras.Model(ts_inputs, generator_output, name="generator")

    x = keras.layers.Conv1D(64, kernel_size=5, strides=2, padding="SAME", activation=keras.layers.LeakyReLU(0.2))(ts_inputs)
    x = keras.layers.Dropout(0.4)(x)
    x = keras.layers.Conv1D(128, kernel_size=5, strides=2, padding="SAME", activation=keras.layers.LeakyReLU(0.2))(x)
    x = keras.layers.Dropout(0.4)(x)
    x = keras.layers.Flatten()(x)
    discriminator_output = keras.layers.Dense(1, activation="sigmoid")(x)
    discriminator = keras.Model(ts_inputs, discriminator_output, name="discriminator")

    gan = keras.models.Sequential([generator, discriminator])

    discriminator.compile(loss='categorical_crossentropy', optimizer="adam")
    discriminator.trainable = False
    gan.compile(loss="binary_crossentropy", optimizer="adam")
    return temporal, gan


#################################Skip-RNN Model#################################
# Skip-RNN
class SkipRNN(tf.keras.layers.Layer):
    def __init__(self, cell, return_sequences=False, **kwargs):
        super().__init__(**kwargs)
        self.cell = cell
        self.return_sequences = return_sequences
        self.get_initial_state = getattr(
            self.cell, "get_initial_state", self.fallback_initial_state)
    def fallback_initial_state(self, inputs):
        return [tf.zeros([self.cell.state_size], dtype=inputs.dtype)]

    def call(self, inputs, states=None):
        states = self.get_initial_state(inputs) if states == None else states

        outputs = tf.zeros(shape=[self.cell.output_size], dtype=inputs.dtype)
        outputs, states = self.cell(inputs, states)

        return outputs, states
    
def Modified_S_RNN(X_train):
    tf.keras.backend.clear_session()

    sparseness_weights = [(0, 1), (1, 0), (1, 1)]
    BATCH_SIZE = 128
    N, N_LAYERS, N_UNITS = 3, 1, 32

    X_train_reverse = np.flip(X_train, axis=1)
    seq_length, dim = X_train.shape[1], X_train.shape[2]

    en_input = Input(shape=[seq_length, dim])
    X = layers.GaussianNoise(0.1)(en_input)
    initial_states = tf.zeros([BATCH_SIZE, N_UNITS])

    shared_latents = []
    for i in range(N):
        prev_states = []
        skip_length = 2**i
        w1, w2 = np.array(sparseness_weights)[np.random.choice(3, size=1)][0]
        w = w1 + w2

        for t in range(seq_length):
            Xt = layers.Lambda(lambda x: x[:, t, :])(X)
            if t == 0:
                O, H = SkipRNN(layers.GRUCell(N_UNITS))(Xt)
            else:
                if t - skip_length >= 0:
                    states = (w1 * prev_states[t-1] + w2 * prev_states[t-skip_length]) / w
                    O, H = SkipRNN(layers.GRUCell(N_UNITS))(Xt, prev_states[t-1])
                else:
                    O, H = SkipRNN(layers.GRUCell(N_UNITS))(Xt, prev_states[t-1])

            prev_states.append(H)
        shared_latents.append(H)

    de_outputs = []
    de_input = layers.Concatenate()(shared_latents)
    D_shared = layers.Dense(dim, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.005))(de_input)

    for i in range(N):
        Y_i = []
        prev_states = []
        skip_length = 2**i
        w1, w2 = np.array(sparseness_weights)[np.random.choice(3, size=1)][0]
        w = w1 + w2
        
        D_each = layers.Dense(dim, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.005))(shared_latents[i])

        D = layers.Concatenate()([D_shared, D_each])
        D = layers.Dense(dim)(D)

        for t in range(seq_length):
            if t == 0:
                y = layers.Dense(dim)(D)
                _, H = SkipRNN(layers.GRUCell(dim))(y, D) # y_t
            else:
                if t - skip_length >= 0:
                    states = (w1 * prev_states[t-1] + w2 * prev_states[t-skip_length]) / w
                    y, H = SkipRNN(layers.GRUCell(dim))(Y_i[t-1], states) # y_t-1 --> y_1
                else:
                    y, H = SkipRNN(layers.GRUCell(dim))(Y_i[t-1], prev_states[t-1]) # y_t-1 --> y_1

            Y_i.append(y)
            prev_states.append(H)

        Y_i = layers.Concatenate()(Y_i)
        Y_i = layers.Reshape([seq_length, dim])(Y_i)
        de_outputs.append(Y_i)

    model = Model(inputs=en_input, outputs=de_outputs)
    
    lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay( initial_learning_rate=0.001, decay_steps=10000, decay_rate=0.9)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=lr_schedule, clipnorm=2.5), loss='mse')

    history = model.fit(X_train, [X_train_reverse for _ in range(N)], batch_size=BATCH_SIZE, epochs=50, validation_split=0.3, verbose=0, callbacks=[tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min", restore_best_weights=True)]) 
    return model