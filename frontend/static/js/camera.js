/**
 * camera.js - 摄像头控制脚本
 * 提供摄像头测试、实时预览、拍照和图片管理功能
 */

class CameraController {
    constructor() {
        this.videoElement = null;
        this.canvasElement = null;
        this.stream = null;
        this.isStreaming = false;
        this.deviceId = this.getDeviceIdFromUrl();

        this.init();
    }

    getDeviceIdFromUrl() {
        // 从URL路径中提取设备ID
        const path = window.location.pathname;
        const match = path.match(/\/camera\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    init() {
        this.bindElements();
        this.bindEvents();
        this.updateCameraStatus('就绪');
    }

    bindElements() {
        this.cameraStatus = document.getElementById('cameraStatus');
        this.liveFeed = document.getElementById('liveFeed');
        this.placeholderImg = document.getElementById('placeholderImg');
        this.testResult = document.getElementById('testResult');
        this.galleryGrid = document.getElementById('galleryGrid');
        this.imageCount = document.getElementById('imageCount');

        // 按钮
        this.testCameraBtn = document.getElementById('testCameraBtn');
        this.startCameraBtn = document.getElementById('startCameraBtn');
        this.captureBtn = document.getElementById('captureBtn');
        this.stopCameraBtn = document.getElementById('stopCameraBtn');
        this.refreshGalleryBtn = document.getElementById('refreshGalleryBtn');
    }

    bindEvents() {
        this.testCameraBtn.addEventListener('click', () => this.testCamera());
        this.startCameraBtn.addEventListener('click', () => this.startCamera());
        this.captureBtn.addEventListener('click', () => this.captureImage());
        this.stopCameraBtn.addEventListener('click', () => this.stopCamera());
        this.refreshGalleryBtn.addEventListener('click', () => this.refreshGallery());

        // 页面卸载时停止摄像头
        window.addEventListener('beforeunload', () => this.stopCamera());
    }

    updateCameraStatus(status, type = 'info') {
        if (this.cameraStatus) {
            this.cameraStatus.textContent = status;
            this.cameraStatus.className = `camera-status status-${type}`;
        }
    }

    async testCamera() {
        this.updateCameraStatus('测试中...', 'warning');
        this.testResult.innerHTML = '<div class="loading">正在测试摄像头...</div>';

        try {
            // 检查摄像头权限
            const permission = await navigator.permissions.query({ name: 'camera' });

            if (permission.state === 'denied') {
                throw new Error('摄像头权限被拒绝，请在浏览器设置中允许摄像头访问');
            }

            // 尝试获取摄像头设备列表
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');

            if (videoDevices.length === 0) {
                throw new Error('未检测到摄像头设备');
            }

            // 测试摄像头访问
            const testStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }
            });

            // 立即停止测试流
            testStream.getTracks().forEach(track => track.stop());

            this.updateCameraStatus('测试成功', 'success');
            this.testResult.innerHTML = `
                <div class="test-success">
                    <h4>✅ 摄像头测试成功</h4>
                    <p>检测到 ${videoDevices.length} 个摄像头设备</p>
                    <ul>
                        ${videoDevices.map((device, index) =>
                            `<li>摄像头 ${index + 1}: ${device.label || '未命名设备'}</li>`
                        ).join('')}
                    </ul>
                </div>
            `;

        } catch (error) {
            console.error('摄像头测试失败:', error);
            this.updateCameraStatus('测试失败', 'error');
            this.testResult.innerHTML = `
                <div class="test-error">
                    <h4>❌ 摄像头测试失败</h4>
                    <p>错误信息: ${error.message}</p>
                    <div class="error-tips">
                        <h5>解决建议:</h5>
                        <ul>
                            <li>确保摄像头已正确连接</li>
                            <li>检查浏览器摄像头权限设置</li>
                            <li>尝试刷新页面重新授权</li>
                            <li>如果使用HTTPS，确保证书有效</li>
                        </ul>
                    </div>
                </div>
            `;
        }
    }

    async startCamera() {
        if (this.isStreaming) {
            this.updateCameraStatus('摄像头已在运行', 'warning');
            return;
        }

        try {
            this.updateCameraStatus('启动中...', 'warning');

            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'environment' // 优先使用后置摄像头
                }
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);

            // 创建video元素显示摄像头画面
            if (!this.videoElement) {
                this.videoElement = document.createElement('video');
                this.videoElement.autoplay = true;
                this.videoElement.playsInline = true;
                this.videoElement.style.width = '100%';
                this.videoElement.style.height = '100%';
                this.videoElement.style.objectFit = 'cover';
                this.videoElement.style.borderRadius = '8px';

                const container = document.getElementById('videoContainer');
                container.innerHTML = '';
                container.appendChild(this.videoElement);
            }

            this.videoElement.srcObject = this.stream;
            this.isStreaming = true;

            this.updateCameraStatus('运行中', 'success');
            this.captureBtn.disabled = false;
            this.startCameraBtn.disabled = true;
            this.stopCameraBtn.disabled = false;

        } catch (error) {
            console.error('启动摄像头失败:', error);
            this.updateCameraStatus('启动失败', 'error');
            alert(`启动摄像头失败: ${error.message}`);
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.videoElement) {
            this.videoElement.srcObject = null;
        }

        this.isStreaming = false;
        this.updateCameraStatus('已停止', 'info');
        this.captureBtn.disabled = true;
        this.startCameraBtn.disabled = false;
        this.stopCameraBtn.disabled = true;

        // 恢复占位图片
        const container = document.getElementById('videoContainer');
        container.innerHTML = `
            <img id="liveFeed" src="" alt="摄像头画面" style="display: none;">
            <div class="placeholder-image" id="placeholderImg">
                <div class="placeholder-icon">📷</div>
                <p>摄像头未启动或不可用</p>
            </div>
        `;
        this.placeholderImg = document.getElementById('placeholderImg');
    }

    async captureImage() {
        if (!this.isStreaming || !this.videoElement) {
            alert('请先启动摄像头');
            return;
        }

        try {
            // 创建canvas来捕获图像
            if (!this.canvasElement) {
                this.canvasElement = document.createElement('canvas');
                this.canvasElement.style.display = 'none';
                document.body.appendChild(this.canvasElement);
            }

            const context = this.canvasElement.getContext('2d');
            this.canvasElement.width = this.videoElement.videoWidth;
            this.canvasElement.height = this.videoElement.videoHeight;

            // 绘制当前视频帧到canvas
            context.drawImage(this.videoElement, 0, 0);

            // 转换为blob
            this.canvasElement.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob, `capture_${Date.now()}.jpg`);
                formData.append('device_id', this.deviceId);

                try {
                    const response = await fetch('/api/camera/capture', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        alert('照片保存成功！');
                        this.refreshGallery();
                    } else {
                        alert('保存失败: ' + result.error);
                    }
                } catch (error) {
                    console.error('上传照片失败:', error);
                    alert('上传失败: ' + error.message);
                }
            }, 'image/jpeg', 0.8);

        } catch (error) {
            console.error('拍照失败:', error);
            alert('拍照失败: ' + error.message);
        }
    }

    async refreshGallery() {
        try {
            const response = await fetch(`/api/camera/images/${this.deviceId}`);
            const result = await response.json();

            if (result.success) {
                this.updateGallery(result.images);
            } else {
                console.error('获取图片列表失败:', result.error);
            }
        } catch (error) {
            console.error('刷新图片库失败:', error);
        }
    }

    updateGallery(images) {
        this.imageCount.textContent = images.length;

        if (images.length === 0) {
            this.galleryGrid.innerHTML = '<div class="gallery-empty">暂无保存的图片</div>';
            return;
        }

        const imageHtml = images.map(image => `
            <div class="gallery-item">
                <img src="/static/uploads/camera/${image.filename}"
                     alt="${image.filename}"
                     onclick="window.open(this.src)">
                <div class="image-info">
                    <small>${new Date(image.timestamp).toLocaleString()}</small>
                </div>
            </div>
        `).join('');

        this.galleryGrid.innerHTML = imageHtml;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查浏览器支持
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('您的浏览器不支持摄像头功能，请使用现代浏览器（如Chrome、Firefox、Safari）');
        return;
    }

    // 初始化摄像头控制器
    new CameraController();
});
