/**
 * static/js/voice.js — Web Speech API Client
 * =========================================
 * Provides hands-free Speech-to-Text (recognition)
 * and Text-to-Speech (reading responses aloud).
 */

class VoiceManager {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.ttsEnabled = false;
        this.activeUtterance = null;
        
        this.initRecognition();
    }

    initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Speech Recognition API is not supported in this browser.");
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = "en-US";
    }

    startListening(onResult, onStart, onEnd) {
        if (!this.recognition) return;
        if (this.isListening) {
            this.recognition.stop();
            return;
        }

        this.recognition.onstart = () => {
            this.isListening = true;
            if (onStart) onStart();
        };

        this.recognition.onend = () => {
            this.isListening = false;
            if (onEnd) onEnd();
        };

        this.recognition.onerror = (e) => {
            console.error("Speech recognition error:", e);
            this.recognition.stop();
        };

        this.recognition.onresult = (event) => {
            const resultText = event.results[0][0].transcript;
            if (onResult) onResult(resultText);
        };

        this.recognition.start();
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    speak(text) {
        if (!this.synthesis || !this.ttsEnabled) return;
        this.stopSpeaking();
        
        // Strip markdown before speaking
        const plainText = text.replace(/[*#`_\-]/g, "");

        this.activeUtterance = new SpeechSynthesisUtterance(plainText);
        this.activeUtterance.lang = "en-US";
        this.synthesis.speak(this.activeUtterance);
    }

    stopSpeaking() {
        if (this.synthesis && this.synthesis.speaking) {
            this.synthesis.cancel();
        }
    }

    toggleTTS(onToggle) {
        this.ttsEnabled = !this.ttsEnabled;
        if (!this.ttsEnabled) {
            this.stopSpeaking();
        }
        if (onToggle) onToggle(this.ttsEnabled);
        return this.ttsEnabled;
    }
}
