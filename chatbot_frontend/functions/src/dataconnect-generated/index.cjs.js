const { queryRef, executeQuery, mutationRef, executeMutation, validateArgs } = require('firebase/data-connect');

const connectorConfig = {
  connector: 'example',
  service: 'chatbotfrontend',
  location: 'us-central1'
};
exports.connectorConfig = connectorConfig;

const createNewAgentRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateNewAgent', inputVars);
}
createNewAgentRef.operationName = 'CreateNewAgent';
exports.createNewAgentRef = createNewAgentRef;

exports.createNewAgent = function createNewAgent(dcOrVars, vars) {
  return executeMutation(createNewAgentRef(dcOrVars, vars));
};

const getMyAgentsRef = (dc) => {
  const { dc: dcInstance} = validateArgs(connectorConfig, dc, undefined);
  dcInstance._useGeneratedSdk();
  return queryRef(dcInstance, 'GetMyAgents');
}
getMyAgentsRef.operationName = 'GetMyAgents';
exports.getMyAgentsRef = getMyAgentsRef;

exports.getMyAgents = function getMyAgents(dc) {
  return executeQuery(getMyAgentsRef(dc));
};

const updateAgentRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'UpdateAgent', inputVars);
}
updateAgentRef.operationName = 'UpdateAgent';
exports.updateAgentRef = updateAgentRef;

exports.updateAgent = function updateAgent(dcOrVars, vars) {
  return executeMutation(updateAgentRef(dcOrVars, vars));
};

const deleteAgentRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'DeleteAgent', inputVars);
}
deleteAgentRef.operationName = 'DeleteAgent';
exports.deleteAgentRef = deleteAgentRef;

exports.deleteAgent = function deleteAgent(dcOrVars, vars) {
  return executeMutation(deleteAgentRef(dcOrVars, vars));
};
