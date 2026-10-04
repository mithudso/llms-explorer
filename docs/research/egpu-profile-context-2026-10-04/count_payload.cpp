// CPU-only vocabulary/template measurement. No context, weights or inference.
#include "server-chat.h"
#include "server-common.h"
#include "common.h"
#include "llama.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <iterator>

int main(int argc, char **argv) {
    try {
        if (argc != 5) throw std::runtime_error("usage: count_payload convert|count model request output");
        std::ifstream stream(argv[3]);
        const std::string raw((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
        json request = json::parse(raw);
        if (std::string(argv[1]) == "convert") {
            std::ofstream(argv[4]) << server_chat_convert_anthropic_to_oai(request).dump(2) << "\n";
            return 0;
        }
        if (std::string(argv[1]) != "count") throw std::runtime_error("invalid mode");
        llama_model_params params = llama_model_default_params();
        params.vocab_only = true;
        params.n_gpu_layers = 0;
        auto *model = llama_model_load_from_file(argv[2], params);
        if (!model) throw std::runtime_error("vocabulary load failed");
        auto *vocab = llama_model_get_vocab(model);
        server_chat_params options{};
        options.use_jinja = true;
        options.prefill_assistant = false;
        options.reasoning_format = COMMON_REASONING_FORMAT_DEEPSEEK;
        options.enable_thinking = true;
        options.tmpls = common_chat_templates_init(model, "");
        std::vector<raw_buffer> files;
        const auto rendered = oaicompat_chat_params_parse(request, options, files);
        if (!files.empty()) throw std::runtime_error("multimodal input is outside this measurement");
        const auto prompt = rendered.at("prompt").get<std::string>();
        const auto tokens = common_tokenize(vocab, prompt, true, true);
        json result = {
            {"scope", "CPU vocabulary-only; offline server template rendering"},
            {"model_path", argv[2]}, {"rendered_prompt_bytes", prompt.size()},
            {"rendered_prompt_tokens", tokens.size()}, {"tools", request.at("tools").size()},
            {"vocab_only", true}, {"model_contexts_created", 0}, {"inference_calls", 0},
            {"gpu_layers", 0}, {"prompt", prompt}
        };
        std::ofstream(argv[4]) << result.dump(2) << "\n";
        std::cout << "prompt_tokens=" << tokens.size() << " tools=" << request.at("tools").size() << "\n";
        llama_model_free(model);
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << "\n";
        return 2;
    }
}
