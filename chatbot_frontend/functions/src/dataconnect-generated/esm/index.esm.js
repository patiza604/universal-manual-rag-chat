import { queryRef, executeQuery, mutationRef, executeMutation, validateArgs } from 'firebase/data-connect';

export const connectorConfig = {
  connector: 'example',
  service: 'chatbotfrontend',
  location: 'us-central1'
};

export const createNewAgentRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateNewAgent', inputVars);
}
createNewAgentRef.operationName = 'CreateNewAgent';

export function createNewAgent(dcOrVars, vars) {
  return executeMutation(createNewAgentRef(dcOrVars, vars));
}

export const getMyAgentsRef = (dc) => {
  const { dc: dcInstance} = validateArgs(connectorConfig, dc, undefined);
  dcInstance._useGeneratedSdk();
  return queryRef(dcInstance, 'GetMyAgents');
}
getMyAgentsRef.operationName = 'GetMyAgents';

export function getMyAgents(dc) {
  return executeQuery(getMyAgentsRef(dc));
}

export const updateAgentRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'UpdateAgent', inputVars);
}
updateAgentRef.operationName = 'UpdateAgent';

export function updateAgent(dcOrVars, vars) {
  return executeMutation(updateAgentRef(dcOrVars, vars));
}

export const deleteAgentRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'DeleteAgent', inputVars);
}
deleteAgentRef.operationName = 'DeleteAgent';

export function deleteAgent(dcOrVars, vars) {
  return executeMutation(deleteAgentRef(dcOrVars, vars));
}

