// HLS C++ — 1N4007 IV-curve approximator
// Quantization: int8
#include "myproject.h"
#include "weights/weights.h"

void myproject(data_t input[N_INPUTS], result_t output[N_OUTPUTS]) {
#pragma HLS PIPELINE II=1
#pragma HLS ARRAY_PARTITION variable=input complete

    // Layer 1: Dense(64)
    static data_t layer1_out[64];
    #pragma HLS ARRAY_PARTITION variable=layer1_out complete
    for (int j = 0; j < 64; j++) {
        accum_t acc = bias1[j];
        for (int k = 0; k < 1; k++)
            acc += weight1[k][j] * (input[k]);
        layer1_out[j] = (j < 64) ? (acc > 0 ? acc : (accum_t)0) : acc;  // ReLU sauf dernier
    }

    // Layer 2: Dense(128)
    static data_t layer2_out[128];
    #pragma HLS ARRAY_PARTITION variable=layer2_out complete
    for (int j = 0; j < 128; j++) {
        accum_t acc = bias2[j];
        for (int k = 0; k < 64; k++)
            acc += weight2[k][j] * (layer1_out[k]);
        layer2_out[j] = (j < 128) ? (acc > 0 ? acc : (accum_t)0) : acc;  // ReLU sauf dernier
    }

    // Layer 3: Dense(128)
    static data_t layer3_out[128];
    #pragma HLS ARRAY_PARTITION variable=layer3_out complete
    for (int j = 0; j < 128; j++) {
        accum_t acc = bias3[j];
        for (int k = 0; k < 128; k++)
            acc += weight3[k][j] * (layer2_out[k]);
        layer3_out[j] = (j < 128) ? (acc > 0 ? acc : (accum_t)0) : acc;  // ReLU sauf dernier
    }

    // Layer 4: Dense(64)
    static data_t layer4_out[64];
    #pragma HLS ARRAY_PARTITION variable=layer4_out complete
    for (int j = 0; j < 64; j++) {
        accum_t acc = bias4[j];
        for (int k = 0; k < 128; k++)
            acc += weight4[k][j] * (layer3_out[k]);
        layer4_out[j] = (j < 64) ? (acc > 0 ? acc : (accum_t)0) : acc;  // ReLU sauf dernier
    }

    // Layer 5: Dense(32)
    static data_t layer5_out[32];
    #pragma HLS ARRAY_PARTITION variable=layer5_out complete
    for (int j = 0; j < 32; j++) {
        accum_t acc = bias5[j];
        for (int k = 0; k < 64; k++)
            acc += weight5[k][j] * (layer4_out[k]);
        layer5_out[j] = (j < 32) ? (acc > 0 ? acc : (accum_t)0) : acc;  // ReLU sauf dernier
    }

    // Layer 6: Dense(1)
    static data_t layer6_out[1];
    #pragma HLS ARRAY_PARTITION variable=layer6_out complete
    for (int j = 0; j < 1; j++) {
        accum_t acc = bias6[j];
        for (int k = 0; k < 32; k++)
            acc += weight6[k][j] * (layer5_out[k]);
        layer6_out[j] = (j < 1) ? (acc > 0 ? acc : (accum_t)0) : acc;  // ReLU sauf dernier
    }

    output[0] = layer6_out[0];
}