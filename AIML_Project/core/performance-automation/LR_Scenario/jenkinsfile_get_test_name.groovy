        stage('Get Test Name') {
            steps {
                script {
                    def runId = sh(script: "cat ${WORKSPACE}/results/run_id.txt", returnStdout: true).trim()
                    def pcCookie = sh(script: "cat ${WORKSPACE}/results/pc_cookie.txt", returnStdout: true).trim()
                    
                    echo ""
                    echo "=" * 60
                    echo "Getting Test Name"
                    echo "=" * 60
                    
                    // Method 1: Get test name from Tests endpoint using TEST_ID
                    echo "Fetching test details for Test ID: ${params.TEST_ID}"
                    
                    def testDetailsXml = sh(
                        script: """
                            curl -k -s \
                            "https://${params.PC_HOST}:${params.PC_PORT}/LoadTest/rest/domains/${params.PC_DOMAIN}/projects/${params.PC_PROJECT}/Tests/${params.TEST_ID}" \
                            -H "Cookie: ${pcCookie}" \
                            -H "Accept: application/xml"
                        """,
                        returnStdout: true
                    ).trim()
                    
                    // Save test details XML
                    sh "echo '${testDetailsXml}' > ${WORKSPACE}/results/test_details.xml"
                    
                    echo "Test details XML received (length: ${testDetailsXml.length()})"
                    
                    // Extract test name from XML
                    // PC uses <n> tag for test name in Tests endpoint
                    def testName = sh(
                        script: """
                            # Try to extract test name from <n> tag
                            TEST_NAME=\$(echo '${testDetailsXml}' | grep -oP '<n>\\K[^<]+' | head -1)
                            
                            # If not found, try <TestName> tag
                            if [ -z "\$TEST_NAME" ]; then
                                TEST_NAME=\$(echo '${testDetailsXml}' | grep -oP '<TestName>\\K[^<]+' | head -1)
                            fi
                            
                            # If not found, try <n> tag
                            if [ -z "\$TEST_NAME" ]; then
                                TEST_NAME=\$(echo '${testDetailsXml}' | grep -oP '<n>\\K[^<]+' | head -1)
                            fi
                            
                            # If still not found, use default
                            if [ -z "\$TEST_NAME" ]; then
                                TEST_NAME="Test_${params.TEST_ID}"
                            fi
                            
                            echo "\$TEST_NAME"
                        """,
                        returnStdout: true
                    ).trim()
                    
                    echo "Test Name: ${testName}"
                    
                    // Save test name to file
                    sh "echo '${testName}' > ${WORKSPACE}/results/test_name.txt"
                    
                    // Method 2: Also try to get from run details as fallback
                    def runDetailsXml = sh(
                        script: """
                            curl -k -s \
                            "https://${params.PC_HOST}:${params.PC_PORT}/LoadTest/rest/domains/${params.PC_DOMAIN}/projects/${params.PC_PROJECT}/Runs/${runId}" \
                            -H "Cookie: ${pcCookie}" \
                            -H "Accept: application/xml" 2>/dev/null || echo ""
                        """,
                        returnStdout: true
                    ).trim()
                    
                    if (runDetailsXml && runDetailsXml.length() > 100) {
                        sh "echo '${runDetailsXml}' > ${WORKSPACE}/results/run_details.xml"
                        
                        // Try to extract test name from run details if we got default
                        if (testName == "Test_${params.TEST_ID}") {
                            def runTestName = sh(
                                script: """
                                    RUN_TEST=\$(echo '${runDetailsXml}' | grep -oP '<TestName>\\K[^<]+' | head -1)
                                    if [ -z "\$RUN_TEST" ]; then
                                        RUN_TEST=\$(echo '${runDetailsXml}' | grep -oP '<n>\\K[^<]+' | head -1)
                                    fi
                                    echo "\$RUN_TEST"
                                """,
                                returnStdout: true
                            ).trim()
                            
                            if (runTestName) {
                                echo "Test Name from Run Details: ${runTestName}"
                                testName = runTestName
                                sh "echo '${testName}' > ${WORKSPACE}/results/test_name.txt"
                            }
                        }
                    }
                    
                    echo ""
                    echo "✓ Test Name captured: ${testName}"
                    echo ""
                }
            }
        }
