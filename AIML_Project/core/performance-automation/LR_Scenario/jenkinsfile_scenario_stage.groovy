// Jenkinsfile snippet - Add this stage after "Trigger Test" stage and before "Monitor Execution"

        stage('Get Scenario Name') {
            steps {
                script {
                    def runId = sh(script: "cat ${WORKSPACE}/results/run_id.txt", returnStdout: true).trim()
                    def pcCookie = sh(script: "cat ${WORKSPACE}/results/pc_cookie.txt", returnStdout: true).trim()
                    
                    echo ""
                    echo "=" * 60
                    echo "Getting Scenario Details"
                    echo "=" * 60
                    
                    // Get run details to extract scenario name
                    def runDetailsXml = sh(
                        script: """
                            curl -k -s \
                            "https://${params.PC_HOST}:${params.PC_PORT}/LoadTest/rest/domains/${params.PC_DOMAIN}/projects/${params.PC_PROJECT}/Runs/${runId}" \
                            -H "Cookie: ${pcCookie}" \
                            -H "Accept: application/xml"
                        """,
                        returnStdout: true
                    ).trim()
                    
                    // Save run details XML
                    sh "echo '${runDetailsXml}' > ${WORKSPACE}/results/run_details.xml"
                    
                    echo "Run details XML received (length: ${runDetailsXml.length()})"
                    
                    // Extract scenario name from XML - try multiple field names
                    def scenarioName = sh(
                        script: """
                            # Try multiple XML tags that PC might use
                            SCENARIO=\$(echo '${runDetailsXml}' | grep -oP '<TestName>\\K[^<]+' | head -1)
                            if [ -z "\$SCENARIO" ]; then
                                SCENARIO=\$(echo '${runDetailsXml}' | grep -oP '<ScenarioName>\\K[^<]+' | head -1)
                            fi
                            if [ -z "\$SCENARIO" ]; then
                                SCENARIO=\$(echo '${runDetailsXml}' | grep -oP '<n>\\K[^<]+' | head -1)
                            fi
                            if [ -z "\$SCENARIO" ]; then
                                SCENARIO=\$(echo '${runDetailsXml}' | grep -oP '<name>\\K[^<]+' | head -1)
                            fi
                            if [ -z "\$SCENARIO" ]; then
                                SCENARIO="Test_${params.TEST_ID}"
                            fi
                            echo "\$SCENARIO"
                        """,
                        returnStdout: true
                    ).trim()
                    
                    echo "Scenario Name: ${scenarioName}"
                    
                    // Save scenario name to file
                    sh "echo '${scenarioName}' > ${WORKSPACE}/results/scenario_name.txt"
                    
                    // Also try to get test name from test details endpoint
                    echo ""
                    echo "Fetching test metadata for Test ID: ${params.TEST_ID}"
                    
                    def testDetailsXml = sh(
                        script: """
                            curl -k -s \
                            "https://${params.PC_HOST}:${params.PC_PORT}/LoadTest/rest/domains/${params.PC_DOMAIN}/projects/${params.PC_PROJECT}/Tests/${params.TEST_ID}" \
                            -H "Cookie: ${pcCookie}" \
                            -H "Accept: application/xml" 2>/dev/null || echo ""
                        """,
                        returnStdout: true
                    ).trim()
                    
                    if (testDetailsXml && testDetailsXml.length() > 100) {
                        sh "echo '${testDetailsXml}' > ${WORKSPACE}/results/test_details.xml"
                        
                        // Extract test name from test details
                        def testName = sh(
                            script: """
                                TEST_NAME=\$(echo '${testDetailsXml}' | grep -oP '<n>\\K[^<]+' | head -1)
                                if [ -z "\$TEST_NAME" ]; then
                                    TEST_NAME=\$(echo '${testDetailsXml}' | grep -oP '<name>\\K[^<]+' | head -1)
                                fi
                                echo "\$TEST_NAME"
                            """,
                            returnStdout: true
                        ).trim()
                        
                        if (testName) {
                            echo "Test Name from Test Details: ${testName}"
                            // Use test name if scenario name wasn't found
                            if (scenarioName == "Test_${params.TEST_ID}") {
                                scenarioName = testName
                                sh "echo '${testName}' > ${WORKSPACE}/results/scenario_name.txt"
                            }
                        }
                    }
                    
                    echo ""
                    echo "✓ Scenario Name captured: ${scenarioName}"
                    echo ""
                }
            }
        }
