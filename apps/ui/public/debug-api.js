// 测试API客户端
async function testApiClient() {
    console.log('=== API客户端测试开始 ===');
    
    try {
        console.log('1. 直接调用API端点...');
        const response = await fetch('http://localhost:8001/api/running/instances');
        console.log('原始响应:', response);
        
        const rawData = await response.json();
        console.log('2. 原始API数据:', rawData);
        
        // 模拟apiClient.get的处理逻辑
        console.log('3. 检查数据结构...');
        if (rawData.success && rawData.data) {
            console.log('✅ 数据格式正确');
            console.log('4. 实例数据:', rawData.data.instances);
            console.log('5. 实例数量:', rawData.data.instances.length);
            
            // 模拟ApiContext的处理
            console.log('6. 模拟updateData调用...');
            const instances = rawData.data.instances;
            console.log('7. 保存到状态的实例:', instances);
            
            // 模拟CurrentRunning组件的处理
            console.log('8. 模拟组件处理...');
            const typedApiInstances = instances || [];
            console.log('9. typedApiInstances:', typedApiInstances);
            
            if (typedApiInstances.length > 0) {
                console.log('✅ 成功！应该显示', typedApiInstances.length, '个实例');
            } else {
                console.log('❌ 失败：实例数组为空');
            }
        } else {
            console.log('❌ 数据格式错误:', rawData);
        }
        
    } catch (error) {
        console.error('❌ API测试失败:', error);
    }
    
    console.log('=== API客户端测试结束 ===');
}

// 运行测试
testApiClient();