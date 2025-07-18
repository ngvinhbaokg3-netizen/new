// Ứng dụng Text-to-Speech tiếng Việt với ElevenLabs
document.addEventListener('DOMContentLoaded', () => {
  // Lấy các phần tử DOM
  const textInput = document.getElementById('textInput');
  const voiceSelect = document.getElementById('voiceSelect');
  const speedRange = document.getElementById('speedRange');
  const speedValue = document.getElementById('speedValue');
  const speakBtn = document.getElementById('speakBtn');
  const stopBtn = document.getElementById('stopBtn');
  const downloadBtn = document.getElementById('downloadBtn');
  const errorMsg = document.getElementById('error-message');
  const statusMsg = document.getElementById('status-message');

  let currentUtterance = null;
  let isPlaying = false;
  let elevenLabsVoices = {};
  let useElevenLabs = false;
  let currentAudioBlob = null;
  let currentFileName = '';

  // Tải danh sách giọng nói ElevenLabs
  async function loadElevenLabsVoices() {
    try {
      const response = await fetch('./voices.json');
      elevenLabsVoices = await response.json();
      console.log('✅ Đã tải danh sách giọng ElevenLabs:', Object.keys(elevenLabsVoices).length, 'giọng');
      console.log('🔍 Debug voices:', elevenLabsVoices);
      
      // Gọi populateVoices sau khi load xong
      populateVoices();
    } catch (error) {
      console.warn('⚠️ Không thể tải voices.json:', error);
      elevenLabsVoices = {};
      populateVoices();
    }
  }

  // Kiểm tra hỗ trợ SpeechSynthesis API
  if (!('speechSynthesis' in window)) {
    showError('Trình duyệt của bạn không hỗ trợ chức năng chuyển văn bản thành giọng nói. Vui lòng sử dụng trình duyệt hiện đại như Chrome, Firefox, Safari hoặc Edge.');
    speakBtn.disabled = true;
    return;
  }

  // Hàm hiển thị lỗi
  function showError(message) {
    errorMsg.textContent = message;
    errorMsg.classList.add('show');
    statusMsg.classList.remove('show');
  }

  // Hàm hiển thị trạng thái
  function showStatus(message) {
    statusMsg.textContent = message;
    statusMsg.classList.add('show');
    errorMsg.classList.remove('show');
  }

  // Hàm ẩn tất cả thông báo
  function hideMessages() {
    errorMsg.classList.remove('show');
    statusMsg.classList.remove('show');
  }

  // Hàm tạo tên file
  function generateFileName(text, voiceName) {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const shortText = text.substring(0, 30).replace(/[^a-zA-Z0-9\u00C0-\u024F\u1E00-\u1EFF]/g, '_');
    const cleanVoiceName = voiceName.replace(/[^a-zA-Z0-9]/g, '_');
    return `TTS_${cleanVoiceName}_${shortText}_${timestamp}.mp3`;
  }

  // Hàm tải xuống file
  function downloadAudio(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Hàm lấy và lọc giọng nói tiếng Việt
  function populateVoices() {
    console.log('🔄 Populating voices...');
    const voices = speechSynthesis.getVoices();
    const vietnameseVoices = voices.filter(voice => 
      voice.lang.toLowerCase().includes('vi') || 
      voice.lang.toLowerCase().includes('vn') ||
      voice.name.toLowerCase().includes('vietnam') ||
      voice.name.toLowerCase().includes('vietnamese')
    );
    
    console.log('🔍 System voices found:', vietnameseVoices.length);
    console.log('🔍 ElevenLabs voices loaded:', Object.keys(elevenLabsVoices).length);
    
    // Xóa các tùy chọn cũ
    voiceSelect.innerHTML = '';
    
    // Thêm nhóm giọng hệ thống
    const systemGroup = document.createElement('optgroup');
    systemGroup.label = '🔊 Giọng nói hệ thống tiếng Việt';
    voiceSelect.appendChild(systemGroup);
    
    // Thêm tùy chọn mặc định
    const defaultOption = document.createElement('option');
    defaultOption.textContent = 'Giọng mặc định tiếng Việt';
    defaultOption.value = 'default';
    defaultOption.dataset.type = 'system';
    systemGroup.appendChild(defaultOption);
    
    // Thêm các giọng tiếng Việt hệ thống
    vietnameseVoices.forEach((voice, index) => {
      const option = document.createElement('option');
      option.textContent = `${voice.name} (${voice.lang})`;
      option.value = voice.name;
      option.dataset.voiceIndex = index;
      option.dataset.type = 'system';
      systemGroup.appendChild(option);
    });
    
    // Thêm thêm giọng giả lập tiếng Việt nếu không có giọng thật
    if (vietnameseVoices.length === 0) {
      const allVoices = voices.filter(voice => 
        voice.lang.toLowerCase().includes('en') ||
        voice.lang.toLowerCase().includes('us') ||
        voice.lang.toLowerCase().includes('gb')
      );
      
      allVoices.slice(0, 5).forEach((voice, index) => {
        const option = document.createElement('option');
        option.textContent = `${voice.name} (Đọc tiếng Việt)`;
        option.value = voice.name;
        option.dataset.voiceIndex = index;
        option.dataset.type = 'system';
        systemGroup.appendChild(option);
      });
    }
    
    // Thêm nhóm giọng ElevenLabs
    if (Object.keys(elevenLabsVoices).length > 0) {
      const elevenGroup = document.createElement('optgroup');
      elevenGroup.label = '🇻🇳 Giọng nói tiếng Việt chất lượng cao (Cần API Key)';
      voiceSelect.appendChild(elevenGroup);
      
      Object.keys(elevenLabsVoices).forEach(voiceName => {
        const option = document.createElement('option');
        option.textContent = voiceName;
        option.value = voiceName;
        option.dataset.type = 'elevenlabs';
        elevenGroup.appendChild(option);
        console.log('➕ Added ElevenLabs voice:', voiceName);
      });
    }
    
    // Hiển thị thông báo
    const totalVoices = Math.max(vietnameseVoices.length, 1) + Object.keys(elevenLabsVoices).length;
    hideMessages();
    showStatus(`Đã tìm thấy ${Math.max(vietnameseVoices.length, 5)} giọng hệ thống và ${Object.keys(elevenLabsVoices).length} giọng tiếng Việt chất lượng cao.`);
    
    console.log('✅ Dropdown populated with', voiceSelect.options.length, 'options');
  }

  // Cập nhật hiển thị tốc độ
  speedRange.addEventListener('input', () => {
    speedValue.textContent = speedRange.value + 'x';
  });

  // Khởi tạo - load ElevenLabs voices trước
  loadElevenLabsVoices();
  
  // Một số trình duyệt tải giọng nói bất đồng bộ
  if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => {
      console.log('🔄 System voices changed, repopulating...');
      populateVoices();
    };
  }

  // Hàm dừng phát âm
  function stopSpeaking() {
    if (speechSynthesis.speaking) {
      speechSynthesis.cancel();
    }
    
    // Dừng ElevenLabs audio nếu đang phát
    if (currentUtterance && currentUtterance instanceof Audio) {
      currentUtterance.pause();
      currentUtterance.currentTime = 0;
    }
    
    isPlaying = false;
    speakBtn.disabled = false;
    stopBtn.disabled = true;
    speakBtn.innerHTML = '<span>▶</span> Tạo Giọng Nói';
    hideMessages();
  }

  // Xử lý sự kiện nút dừng
  stopBtn.addEventListener('click', stopSpeaking);

  // Xử lý sự kiện nút tải xuống
  downloadBtn.addEventListener('click', () => {
    if (currentAudioBlob && currentFileName) {
      downloadAudio(currentAudioBlob, currentFileName);
      showStatus(`✅ Đã tải xuống: ${currentFileName}`);
      setTimeout(() => {
        hideMessages();
      }, 3000);
    } else {
      showError('Không có file audio để tải xuống. Vui lòng tạo giọng nói trước.');
    }
  });

  // Thêm các phần tử DOM cho ElevenLabs
  const apiKeyInput = document.getElementById('apiKeyInput');
  const apiKeyGroup = document.getElementById('apiKeyGroup');

  // Hiển thị/ẩn trường API Key khi chọn giọng ElevenLabs
  voiceSelect.addEventListener('change', () => {
    const selectedOption = voiceSelect.options[voiceSelect.selectedIndex];
    const voiceType = selectedOption?.dataset.type;
    
    console.log('🔄 Voice changed to:', selectedOption?.value, 'Type:', voiceType);
    
    if (voiceType === 'elevenlabs') {
      apiKeyGroup.style.display = 'block';
      useElevenLabs = true;
      console.log('✅ API Key field shown');
    } else {
      apiKeyGroup.style.display = 'none';
      useElevenLabs = false;
      // Reset download button cho giọng hệ thống
      downloadBtn.disabled = true;
      currentAudioBlob = null;
      currentFileName = '';
      console.log('❌ API Key field hidden');
    }
  });

  // Hàm gọi ElevenLabs API
  async function generateElevenLabsTTS(text, voiceName, apiKey) {
    const voiceInfo = elevenLabsVoices[voiceName];
    if (!voiceInfo) {
      throw new Error('Không tìm thấy thông tin giọng nói');
    }

    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceInfo.voice_id}`, {
      method: 'POST',
      headers: {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': apiKey
      },
      body: JSON.stringify({
        text: text,
        model_id: 'eleven_multilingual_v2',
        voice_settings: voiceInfo.settings
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    return response.blob();
  }

  // Xử lý sự kiện nút phát
  speakBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    
    // Kiểm tra văn bản đầu vào
    if (!text) {
      showError('Vui lòng nhập văn bản tiếng Việt trước khi chuyển thành giọng nói.');
      textInput.focus();
      return;
    }

    // Kiểm tra độ dài văn bản
    if (text.length > 5000) {
      showError('Văn bản quá dài. Vui lòng nhập tối đa 5000 ký tự.');
      return;
    }

    const selectedVoiceValue = voiceSelect.value;
    const selectedOption = voiceSelect.options[voiceSelect.selectedIndex];
    const voiceType = selectedOption?.dataset.type;

    console.log('🎤 Starting TTS with voice:', selectedVoiceValue, 'Type:', voiceType);

    // Xử lý ElevenLabs TTS
    if (voiceType === 'elevenlabs') {
      const apiKey = apiKeyInput.value.trim();
      if (!apiKey) {
        showError('Vui lòng nhập API Key ElevenLabs để sử dụng giọng nói chất lượng cao.');
        apiKeyInput.focus();
        return;
      }

      try {
        // Cập nhật UI
        isPlaying = true;
        speakBtn.disabled = true;
        stopBtn.disabled = false;
        downloadBtn.disabled = true;
        speakBtn.innerHTML = '<span>🔊</span> Đang tạo...';
        showStatus('Đang tạo giọng nói chất lượng cao với ElevenLabs...');

        // Gọi API
        const audioBlob = await generateElevenLabsTTS(text, selectedVoiceValue, apiKey);
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Lưu blob và tên file để tải xuống
        currentAudioBlob = audioBlob;
        currentFileName = generateFileName(text, selectedVoiceValue);
        
        // Phát audio
        const audio = new Audio(audioUrl);
        
        audio.onplay = () => {
          speakBtn.innerHTML = '<span>🔊</span> Đang phát...';
          showStatus('Đang phát giọng nói ElevenLabs...');
        };
        
        audio.onended = () => {
          isPlaying = false;
          speakBtn.disabled = false;
          stopBtn.disabled = true;
          downloadBtn.disabled = false; // Kích hoạt nút tải xuống
          speakBtn.innerHTML = '<span>▶</span> Tạo Giọng Nói';
          showStatus('Hoàn thành phát giọng nói ElevenLabs. Bạn có thể tải xuống file MP3.');
          URL.revokeObjectURL(audioUrl);
          
          setTimeout(() => {
            hideMessages();
          }, 5000);
        };
        
        audio.onerror = () => {
          isPlaying = false;
          speakBtn.disabled = false;
          stopBtn.disabled = true;
          downloadBtn.disabled = false; // Vẫn cho phép tải xuống nếu file đã tạo
          speakBtn.innerHTML = '<span>▶</span> Tạo Giọng Nói';
          showError('Lỗi khi phát audio. Nhưng bạn vẫn có thể tải xuống file.');
          URL.revokeObjectURL(audioUrl);
        };

        // Lưu reference để có thể dừng
        currentUtterance = audio;
        audio.play();

      } catch (error) {
        console.error('Lỗi ElevenLabs TTS:', error);
        isPlaying = false;
        speakBtn.disabled = false;
        stopBtn.disabled = true;
        downloadBtn.disabled = true;
        speakBtn.innerHTML = '<span>▶</span> Tạo Giọng Nói';
        
        let errorMessage = error.message;
        if (errorMessage.includes('401')) {
          errorMessage = 'API Key không hợp lệ. Vui lòng kiểm tra lại API Key ElevenLabs.';
        } else if (errorMessage.includes('429')) {
          errorMessage = 'Đã vượt quá giới hạn sử dụng API. Vui lòng thử lại sau.';
        } else if (errorMessage.includes('network')) {
          errorMessage = 'Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet.';
        }
        
        showError(`Lỗi ElevenLabs: ${errorMessage}`);
      }
      return;
    }

    // Xử lý Speech Synthesis API (giọng hệ thống)
    // Reset download cho giọng hệ thống
    downloadBtn.disabled = true;
    currentAudioBlob = null;
    currentFileName = '';
    
    // Dừng phát âm hiện tại nếu có
    if (speechSynthesis.speaking) {
      speechSynthesis.cancel();
    }

    // Tạo utterance mới
    currentUtterance = new SpeechSynthesisUtterance(text);
    
    // Thiết lập ngôn ngữ
    currentUtterance.lang = 'vi-VN';
    
    // Thiết lập tốc độ
    currentUtterance.rate = parseFloat(speedRange.value);
    
    // Thiết lập âm lượng
    currentUtterance.volume = 1;
    
    // Thiết lập cao độ (pitch)
    currentUtterance.pitch = 1;

    // Chọn giọng nói
    if (selectedVoiceValue !== 'default') {
      const voices = speechSynthesis.getVoices();
      const selectedVoice = voices.find(voice => voice.name === selectedVoiceValue);
      if (selectedVoice) {
        currentUtterance.voice = selectedVoice;
      }
    }

    // Xử lý các sự kiện của utterance
    currentUtterance.onstart = () => {
      isPlaying = true;
      speakBtn.disabled = true;
      stopBtn.disabled = false;
      speakBtn.innerHTML = '<span>🔊</span> Đang phát...';
      showStatus('Đang chuyển văn bản thành giọng nói...');
    };

    currentUtterance.onend = () => {
      isPlaying = false;
      speakBtn.disabled = false;
      stopBtn.disabled = true;
      speakBtn.innerHTML = '<span>▶</span> Tạo Giọng Nói';
      showStatus('Hoàn thành chuyển văn bản thành giọng nói.');
      
      // Tự động ẩn thông báo sau 3 giây
      setTimeout(() => {
        hideMessages();
      }, 3000);
    };

    currentUtterance.onerror = (event) => {
      console.error('Lỗi Text-to-Speech:', event.error);
      isPlaying = false;
      speakBtn.disabled = false;
      stopBtn.disabled = true;
      speakBtn.innerHTML = '<span>▶</span> Tạo Giọng Nói';
      
      let errorMessage = 'Đã có lỗi xảy ra trong quá trình chuyển văn bản thành giọng nói.';
      
      // Xử lý các loại lỗi cụ thể
      switch(event.error) {
        case 'network':
          errorMessage = 'Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet.';
          break;
        case 'synthesis-failed':
          errorMessage = 'Không thể tổng hợp giọng nói. Vui lòng thử lại với giọng khác.';
          break;
        case 'synthesis-unavailable':
          errorMessage = 'Dịch vụ tổng hợp giọng nói không khả dụng. Vui lòng thử lại sau.';
          break;
        case 'text-too-long':
          errorMessage = 'Văn bản quá dài để xử lý. Vui lòng rút ngắn nội dung.';
          break;
        case 'rate-not-supported':
          errorMessage = 'Tốc độ phát không được hỗ trợ. Vui lòng điều chỉnh tốc độ.';
          break;
      }
      
      showError(errorMessage);
    };

    currentUtterance.onpause = () => {
      showStatus('Đã tạm dừng phát giọng nói.');
    };

    currentUtterance.onresume = () => {
      showStatus('Tiếp tục phát giọng nói.');
    };

    // Bắt đầu phát
    try {
      speechSynthesis.speak(currentUtterance);
    } catch (error) {
      console.error('Lỗi khi bắt đầu phát:', error);
      showError('Không thể bắt đầu phát giọng nói. Vui lòng thử lại.');
      isPlaying = false;
      speakBtn.disabled = false;
      stopBtn.disabled = true;
      speakBtn.innerHTML = '<span>▶</span> Tạo Giọng Nói';
    }
  });

  // Xử lý phím tắt
  document.addEventListener('keydown', (event) => {
    // Ctrl/Cmd + Enter để phát
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      if (!speakBtn.disabled) {
        speakBtn.click();
      }
    }
    
    // Escape để dừng
    if (event.key === 'Escape') {
      event.preventDefault();
      if (!stopBtn.disabled) {
        stopBtn.click();
      }
    }
    
    // Ctrl/Cmd + D để tải xuống
    if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
      event.preventDefault();
      if (!downloadBtn.disabled) {
        downloadBtn.click();
      }
    }
  });

  // Thêm tooltip cho các nút
  speakBtn.title = 'Phát giọng nói (Ctrl+Enter)';
  stopBtn.title = 'Dừng phát (Escape)';
  downloadBtn.title = 'Tải xuống MP3 (Ctrl+D)';

  // Tự động focus vào textarea khi trang tải
  textInput.focus();

  // Thêm placeholder động
  const placeholders = [
    'Nhập văn bản tiếng Việt để chuyển thành giọng nói...',
    'Ví dụ: Xin chào, tôi là trợ lý ảo của bạn.',
    'Hãy thử nhập một câu thơ hoặc đoạn văn yêu thích...',
    'Bạn có thể nhập tối đa 5000 ký tự.'
  ];

  let placeholderIndex = 0;
  setInterval(() => {
    if (!textInput.value && document.activeElement !== textInput) {
      textInput.placeholder = placeholders[placeholderIndex];
      placeholderIndex = (placeholderIndex + 1) % placeholders.length;
    }
  }, 4000);

  // Đếm ký tự
  const charCounter = document.createElement('div');
  charCounter.style.cssText = `
    text-align: right;
    font-size: 0.85rem;
    color: #666;
    margin-top: 0.25rem;
  `;
  textInput.parentNode.appendChild(charCounter);

  function updateCharCounter() {
    const length = textInput.value.length;
    charCounter.textContent = `${length}/5000 ký tự`;
    
    if (length > 4500) {
      charCounter.style.color = '#e53e3e';
    } else if (length > 4000) {
      charCounter.style.color = '#dd6b20';
    } else {
      charCounter.style.color = '#666';
    }
  }

  textInput.addEventListener('input', updateCharCounter);
  updateCharCounter();

  console.log('🎤 Ứng dụng Text-to-Speech tiếng Việt với tính năng tải xuống đã sẵn sàng! v2.1');
});
