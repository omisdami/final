class RagParameterManager {
    constructor() {
        this.currentParameters = this.getDefaultParameters();
        this.presets = this.loadPresets();
        this.listeners = [];
        this.isGenerating = false;
        this.lastUsedParameters = null;
        this.generationHistory = [];
    }

    getDefaultParameters() {
        return {
            similarity_threshold: 0.6,
            top_k: 5,
            chunk_size: 512,
            overlap: 15
        };
    }

    loadPresets() {
        return {
            default: {
                name: "Default",
                description: "Balanced performance and accuracy",
                parameters: {
                    similarity_threshold: 0.6,
                    top_k: 5,
                    chunk_size: 512,
                    overlap: 15
                }
            },
            high_precision: {
                name: "High Precision",
                description: "More accurate, fewer results",
                parameters: {
                    similarity_threshold: 0.8,
                    top_k: 3,
                    chunk_size: 256,
                    overlap: 10
                }
            },
            comprehensive: {
                name: "Comprehensive",
                description: "More context, broader coverage",
                parameters: {
                    similarity_threshold: 0.5,
                    top_k: 10,
                    chunk_size: 1024,
                    overlap: 20
                }
            },
            fast: {
                name: "Fast",
                description: "Quick results, smaller chunks",
                parameters: {
                    similarity_threshold: 0.7,
                    top_k: 3,
                    chunk_size: 256,
                    overlap: 10
                }
            }
        };
    }

    setParameters(params) {
        const validation = this.validateParameters(params);
        if (!validation.isValid) {
            throw new Error(`Invalid parameters: ${validation.errors.join(", ")}`);
        }
        this.currentParameters = { ...this.currentParameters, ...params };
        this.notifyListeners();
    }

    validateParameters(params) {
        const errors = [];

        if (params.similarity_threshold !== undefined) {
            if (params.similarity_threshold < 0 || params.similarity_threshold > 1) {
                errors.push("Similarity threshold must be between 0.0 and 1.0");
            }
        }

        if (params.top_k !== undefined) {
            if (params.top_k < 1 || params.top_k > 50) {
                errors.push("Top K must be between 1 and 50");
            }
        }

        if (params.chunk_size !== undefined) {
            if (params.chunk_size < 100 || params.chunk_size > 2000) {
                errors.push("Chunk size must be between 100 and 2000");
            }
        }

        if (params.overlap !== undefined) {
            if (params.overlap < 0 || params.overlap > 50) {
                errors.push("Overlap must be between 0 and 50");
            }
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    applyPreset(presetName) {
        const preset = this.presets[presetName];
        if (!this.currentParameters) {
            throw new Error(`Preset '${presetName}' not found`);
        }
        this.currentParameters = { ...preset.parameters };
        this.notifyListeners();
    }

    resetToDefaults() {
        this.currentParameters = this.getDefaultParameters();
        this.notifyListeners();
    }

    setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.notifyListeners();
    }

    recordGeneration(parameters, result) {
        this.lastUsedParameters = { ...parameters };
        this.generationHistory.push({
            timestamp: new Date().toISOString(),
            parameters: { ...parameters },
            result
        });
        if (this.generationHistory.length > 50) {
            this.generationHistory.shift();
        }
    }

    subscribe(listener) {
        this.listeners.push(listener);
    }

    unsubscribe(listener) {
        this.listeners = this.listeners.filter(l => listener !== l);
    }

    notifyListeners() {
        this.listeners.forEach(listener => listener(this.getState()));
    }

    getState() {
        return {
            currentParameters: { ...this.currentParameters },
            presets: this.presets,
            isGenerating: this.isGenerating,
            lastUsedParameters: this.lastUsedParameters,
            generationHistory: [...this.generationHistory]
        };
    }
}
