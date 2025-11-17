rule build_and_merge_qwen:
    conda:
        "envs/huggingface.yml"
    output:
        "qwen2.5-7b-instruct-q5_k_m.gguf"
    shell:
        r"""
        # Clone llama.cpp if missing
        if [ ! -d llama.cpp ]; then
            git clone https://github.com/ggml-org/llama.cpp
        fi

        # Build llama.cpp
        cd llama.cpp
        cmake -B build
        cmake --build build --config Release
        cd ..

        # Download model chunks
        hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
            --include "qwen2.5-7b-instruct-q5_k_m*.gguf" \
            --local-dir .

        # Merge GGUF files
        ./llama.cpp/build/bin/llama-gguf-split \
            --merge qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf \
                    qwen2.5-7b-instruct-q5_k_m.gguf
        """

