const testFrontendBehavior = async () => {
    console.log('=== Testing Frontend API Calls ===');
    
    // 1. Test platforms
    try {
        console.log('1. Testing platforms API...');
        const platformsResponse = await fetch('http://localhost:8001/api/platforms/available');
        console.log('Platforms response status:', platformsResponse.status);
        if (platformsResponse.ok) {
            const platformsData = await platformsResponse.json();
            console.log('Platforms data:', platformsData);
            
            // 2. Test accounts for each platform
            if (platformsData.platforms && platformsData.platforms.length > 0) {
                for (const platform of platformsData.platforms) {
                    console.log(`\n2. Testing accounts for platform: ${platform.id}`);
                    const accountsUrl = `http://localhost:8001/api/accounts/available?platform=${platform.id}`;
                    console.log('Accounts URL:', accountsUrl);
                    
                    const accountsResponse = await fetch(accountsUrl);
                    console.log(`Accounts response status for ${platform.id}:`, accountsResponse.status);
                    
                    if (accountsResponse.ok) {
                        const accountsData = await accountsResponse.json();
                        console.log(`Accounts data for ${platform.id}:`, accountsData);
                        console.log(`Number of accounts for ${platform.id}:`, accountsData.accounts ? accountsData.accounts.length : 0);
                    } else {
                        console.error(`Accounts request failed for ${platform.id}:`, await accountsResponse.text());
                    }
                }
            }
        } else {
            console.error('Platforms request failed:', await platformsResponse.text());
        }
    } catch (error) {
        console.error('Error in API test:', error);
    }
};

// Run the test
testFrontendBehavior();