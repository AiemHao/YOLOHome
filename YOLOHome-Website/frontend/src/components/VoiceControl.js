import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { sendVoiceCommand } from '../services/api';
import RecordRTC from 'recordrtc';
import './VoiceControl.css';

const VoiceControl = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      mediaRecorderRef.current = new RecordRTC(stream, {
        type: 'audio',
        mimeType: 'audio/wav',
        recorderType: RecordRTC.StereoAudioRecorder,
        numberOfAudioChannels: 1,
        desiredSampRate: 16000
      });

      mediaRecorderRef.current.startRecording();
      setIsRecording(true);
      setResult(null);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Không thể truy cập microphone. Vui lòng kiểm tra quyền trình duyệt.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stopRecording(async () => {
        setIsRecording(false);
        const audioBlob = mediaRecorderRef.current.getBlob();
        await handleSendAudio(audioBlob);
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
      });
    }
  };

  const handleSendAudio = async (blob) => {
    setIsLoading(true);
    try {
      const response = await sendVoiceCommand(blob);
      if (response.status === 'success') {
        setResult({
          transcript: response.data.transcript,
          intent: response.data.intent
        });
        // Clear result after 5 seconds
        setTimeout(() => setResult(null), 5000);
      } else {
        alert('Lỗi: ' + (response.message || 'Không thể xử lý giọng nói'));
      }
    } catch (err) {
      console.error('Error sending voice command:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="voice-control-container">
      {result && (
        <div className="voice-result-toast">
          <div className="transcript">"{result.transcript}"</div>
          <div className="intent">
            Đang thực thi: <span>{result.intent.action}</span> {result.intent.device}
          </div>
        </div>
      )}
      
      <button 
        className={`voice-btn ${isRecording ? 'recording' : ''} ${isLoading ? 'loading' : ''}`}
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        disabled={isLoading}
        title="Nhấn và giữ để nói"
      >
        {isLoading ? (
          <Loader2 className="animate-spin" size={24} />
        ) : isRecording ? (
          <Square size={24} />
        ) : (
          <Mic size={24} />
        )}
      </button>
      
      {isRecording && <div className="pulse-ring"></div>}
    </div>
  );
};

export default VoiceControl;
