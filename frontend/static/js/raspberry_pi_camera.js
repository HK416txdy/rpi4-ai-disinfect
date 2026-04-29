/**
 * 树莓派摄像头污渍检测功能
 */

// 当前摄像头状态
let cameraState = {
    initialized: false,
    capturing: false,
    detectorKey: null
};

// 初始化树莓派摄像头
async function initRaspberryPiCamera() {
    console.log('初始化树莓派摄像头...');
    
    const statusDiv = document.getElementById('cameraStatus');
    const resultDiv = document.getElementById('cameraResult');
    
    if (!window.currentMachine) {
        alert('请先选择消毒机');
        return;
    }
    
    try {
        statusDiv.innerHTML = '<div class="alert alert-info">正在初始化摄像头...</div>';
        resultDiv.innerHTML = '';
        
        const response = await fetch('/api/init_raspberry_pi_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                machine_id: window.currentMachine.id,
                machine_name: window.currentMachine.name,
                camera_index: 0  // 默认摄像头索引
            })
        });
        
        const result = await response.json();
        console.log('摄像头初始化结果:', result);
        
        if (result.success) {
            cameraState.initialized = true;
            cameraState.detectorKey = result.detector_key;
            statusDiv.innerHTML = '<div class="alert alert-success">摄像头初始化成功</div>';
            document.getElementById('captureBtn').disabled = false;
            document.getElementById('startContinuousBtn').disabled = false;
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger">初始化失败: ${result.error}</div>`;
            cameraState.initialized = false;
        }
    } catch (error) {
        console.error('摄像头初始化失败:', error);
        statusDiv.innerHTML = `<div class="alert alert-danger">初始化失败: ${error.message}</div>`;
        cameraState.initialized = false;
    }
}

// 捕获单张图像并进行污渍检测
async function captureAndDetectStain() {
    console.log('捕获图像并进行污渍检测...');
    
    const statusDiv = document.getElementById('cameraStatus');
    const resultDiv = document.getElementById('cameraResult');
    
    if (!cameraState.initialized) {
        statusDiv.innerHTML = '<div class="alert alert-warning">请先初始化摄像头</div>';
        return;
    }
    
    try {
        statusDiv.innerHTML = '<div class="alert alert-info">正在捕获图像并进行污渍检测...</div>';
        resultDiv.innerHTML = '';
        
        const response = await fetch('/api/capture_raspberry_pi_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                machine_id: window.currentMachine.id,
                machine_name: window.currentMachine.name,
                method: 'combined'  // 使用组合检测方法
            })
        });
        
        const result = await response.json();
        console.log('污渍检测结果:', result);
        
        if (result.success) {
            statusDiv.innerHTML = '<div class="alert alert-success">检测完成</div>';
            displayRaspberryPiDetectionResult(result);
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger">检测失败: ${result.error}</div>`;
        }
    } catch (error) {
        console.error('捕获图像失败:', error);
        statusDiv.innerHTML = `<div class="alert alert-danger">捕获失败: ${error.message}</div>`;
    }
}

// 开始连续捕获
async function startContinuousCapture() {
    console.log('开始连续捕获...');
    
    const statusDiv = document.getElementById('cameraStatus');
    const resultDiv = document.getElementById('cameraResult');
    
    if (!cameraState.initialized) {
        statusDiv.innerHTML = '<div class="alert alert-warning">请先初始化摄像头</div>';
        return;
    }
    
    try {
        statusDiv.innerHTML = '<div class="alert alert-info">开始连续捕获...</div>';
        
        const response = await fetch('/api/start_continuous_capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                machine_id: window.currentMachine.id,
                machine_name: window.currentMachine.name
            })
        });
        
        const result = await response.json();
        console.log('开始连续捕获结果:', result);
        
        if (result.success) {
            cameraState.capturing = true;
            statusDiv.innerHTML = '<div class="alert alert-success">正在连续捕获中...</div>';
            document.getElementById('stopContinuousBtn').disabled = false;
            document.getElementById('captureBtn').disabled = true;
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger">开始连续捕获失败: ${result.error}</div>`;
        }
    } catch (error) {
        console.error('开始连续捕获失败:', error);
        statusDiv.innerHTML = `<div class="alert alert-danger">开始连续捕获失败: ${error.message}</div>`;
    }
}

// 停止连续捕获
async function stopContinuousCapture() {
    console.log('停止连续捕获...');
    
    const statusDiv = document.getElementById('cameraStatus');
    const resultDiv = document.getElementById('cameraResult');
    
    if (!cameraState.capturing) {
        statusDiv.innerHTML = '<div class="alert alert-warning">未在连续捕获状态</div>';
        return;
    }
    
    try {
        statusDiv.innerHTML = '<div class="alert alert-info">停止连续捕获...</div>';
        
        const response = await fetch('/api/stop_continuous_capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                machine_id: window.currentMachine.id,
                machine_name: window.currentMachine.name
            })
        });
        
        const result = await response.json();
        console.log('停止连续捕获结果:', result);
        
        if (result.success) {
            cameraState.capturing = false;
            statusDiv.innerHTML = '<div class="alert alert-success">已停止连续捕获</div>';
            document.getElementById('stopContinuousBtn').disabled = true;
            document.getElementById('captureBtn').disabled = false;
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger">停止连续捕获失败: ${result.error}</div>`;
        }
    } catch (error) {
        console.error('停止连续捕获失败:', error);
        statusDiv.innerHTML = `<div class="alert alert-danger">停止连续捕获失败: ${error.message}</div>`;
    }
}

// 释放摄像头资源
async function releaseCamera() {
    console.log('释放摄像头资源...');
    
    const statusDiv = document.getElementById('cameraStatus');
    const resultDiv = document.getElementById('cameraResult');
    
    if (!cameraState.initialized) {
        statusDiv.innerHTML = '<div class="alert alert-warning">摄像头未初始化</div>';
        return;
    }
    
    try {
        statusDiv.innerHTML = '<div class="alert alert-info">正在释放摄像头资源...</div>';
        
        const response = await fetch('/api/release_raspberry_pi_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                machine_id: window.currentMachine.id,
                machine_name: window.currentMachine.name
            })
        });
        
        const result = await response.json();
        console.log('释放摄像头结果:', result);
        
        if (result.success) {
            cameraState.initialized = false;
            cameraState.capturing = false;
            cameraState.detectorKey = null;
            statusDiv.innerHTML = '<div class="alert alert-success">摄像头资源已释放</div>';
            document.getElementById('captureBtn').disabled = true;
            document.getElementById('startContinuousBtn').disabled = true;
            document.getElementById('stopContinuousBtn').disabled = true;
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger">释放摄像头失败: ${result.error}</div>`;
        }
    } catch (error) {
        console.error('释放摄像头失败:', error);
        statusDiv.innerHTML = `<div class="alert alert-danger">释放摄像头失败: ${error.message}</div>`;
    }
}

// 显示树莓派摄像头检测结果
function displayRaspberryPiDetectionResult(result) {
    const resultDiv = document.getElementById('cameraResult');
    
    let html = `
        <div class="alert alert-success">
            <div class="text-center mb-3">
                <h6><i class="fas fa-camera"></i> 树莓派摄像头污渍检测结果</h6>
                <small class="text-muted">基于实时捕获图像的分析</small>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <strong>污渍数量:</strong> ${result.stain_count} 个<br>
                    <strong>污渍覆盖率:</strong> ${result.coverage_percentage}%<br>
                    <strong>严重程度评分:</strong> ${result.severity_score}<br>
                    <strong>处理级别:</strong> ${result.recommendation_level}<br>
                </div>
                <div class="col-md-6">
                    <strong>消毒方式:</strong> ${result.cleaning_method}<br>
                    <strong>消毒时间:</strong> ${result.cleaning_time} 分钟<br>
                    <strong>消毒力度:</strong> ${result.cleaning_intensity}<br>
                    <strong>消毒剂用量:</strong> ${result.disinfectant_amount} ml<br>
                </div>
            </div>
            
            <hr>
            
            <h6><i class="fas fa-chart-bar"></i> 灰度分析结果</h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>平均亮度:</strong> ${result.grayscale_analysis.mean_brightness.toFixed(2)}<br>
                    <strong>标准差:</strong> ${result.grayscale_analysis.std_deviation.toFixed(2)}<br>
                    <strong>对比度:</strong> ${result.grayscale_analysis.contrast.toFixed(2)}<br>
                </div>
                <div class="col-md-6">
                    <strong>暗区比例:</strong> ${(result.grayscale_analysis.dark_ratio * 100).toFixed(2)}%<br>
                    <strong>亮区比例:</strong> ${(result.grayscale_analysis.bright_ratio * 100).toFixed(2)}%<br>
                    <strong>均匀性得分:</strong> ${result.grayscale_analysis.uniformity_score.toFixed(2)}<br>
                </div>
            </div>
            
            <hr>
            
            <div class="text-center">
                <small class="text-muted">检测时间: ${new Date().toLocaleString()}</small>
            </div>
        </div>
    `;
    
    resultDiv.innerHTML = html;
}

// 绑定树莓派摄像头事件
function bindRaspberryPiCameraEvents() {
    console.log('绑定树莓派摄像头事件');
    
    // 初始化摄像头按钮
    const initBtn = document.getElementById('initCameraBtn');
    if (initBtn) {
        initBtn.addEventListener('click', initRaspberryPiCamera);
        console.log('初始化摄像头按钮绑定成功');
    }
    
    // 捕获图像按钮
    const captureBtn = document.getElementById('captureBtn');
    if (captureBtn) {
        captureBtn.addEventListener('click', captureAndDetectStain);
        console.log('捕获图像按钮绑定成功');
    }
    
    // 开始连续捕获按钮
    const startContinuousBtn = document.getElementById('startContinuousBtn');
    if (startContinuousBtn) {
        startContinuousBtn.addEventListener('click', startContinuousCapture);
        console.log('开始连续捕获按钮绑定成功');
    }
    
    // 停止连续捕获按钮
    const stopContinuousBtn = document.getElementById('stopContinuousBtn');
    if (stopContinuousBtn) {
        stopContinuousBtn.addEventListener('click', stopContinuousCapture);
        console.log('停止连续捕获按钮绑定成功');
    }
    
    // 释放摄像头按钮
    const releaseBtn = document.getElementById('releaseCameraBtn');
    if (releaseBtn) {
        releaseBtn.addEventListener('click', releaseCamera);
        console.log('释放摄像头按钮绑定成功');
    }
    
    // 初始化时禁用所有功能按钮
    if (captureBtn) captureBtn.disabled = true;
    if (startContinuousBtn) startContinuousBtn.disabled = true;
    if (stopContinuousBtn) stopContinuousBtn.disabled = true;
    if (releaseBtn) releaseBtn.disabled = true;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    bindRaspberryPiCameraEvents();
});