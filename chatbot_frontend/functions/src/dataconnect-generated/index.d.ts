import { ConnectorConfig, DataConnect, QueryRef, QueryPromise, MutationRef, MutationPromise } from 'firebase/data-connect';

export const connectorConfig: ConnectorConfig;

export type TimestampString = string;
export type UUIDString = string;
export type Int64String = string;
export type DateString = string;




export interface AgentRating_Key {
  id: UUIDString;
  __typename?: 'AgentRating_Key';
}

export interface AgentShare_Key {
  id: UUIDString;
  __typename?: 'AgentShare_Key';
}

export interface Agent_Key {
  id: UUIDString;
  __typename?: 'Agent_Key';
}

export interface Conversation_Key {
  id: UUIDString;
  __typename?: 'Conversation_Key';
}

export interface CreateNewAgentData {
  agent_insert: Agent_Key;
}

export interface CreateNewAgentVariables {
  name: string;
  personality: string;
  knowledgeBase?: string | null;
  purpose?: string | null;
  isPublic?: boolean | null;
}

export interface DeleteAgentData {
  agent_delete?: Agent_Key | null;
}

export interface DeleteAgentVariables {
  id: UUIDString;
}

export interface GetMyAgentsData {
  agents: ({
    id: UUIDString;
    name: string;
    personality: string;
    knowledgeBase?: string | null;
    purpose?: string | null;
    isPublic?: boolean | null;
    createdAt: TimestampString;
  } & Agent_Key)[];
}

export interface Message_Key {
  id: UUIDString;
  __typename?: 'Message_Key';
}

export interface UpdateAgentData {
  agent_update?: Agent_Key | null;
}

export interface UpdateAgentVariables {
  id: UUIDString;
  name?: string | null;
  personality?: string | null;
  knowledgeBase?: string | null;
  purpose?: string | null;
  isPublic?: boolean | null;
}

export interface User_Key {
  id: UUIDString;
  __typename?: 'User_Key';
}

interface CreateNewAgentRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateNewAgentVariables): MutationRef<CreateNewAgentData, CreateNewAgentVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: CreateNewAgentVariables): MutationRef<CreateNewAgentData, CreateNewAgentVariables>;
  operationName: string;
}
export const createNewAgentRef: CreateNewAgentRef;

export function createNewAgent(vars: CreateNewAgentVariables): MutationPromise<CreateNewAgentData, CreateNewAgentVariables>;
export function createNewAgent(dc: DataConnect, vars: CreateNewAgentVariables): MutationPromise<CreateNewAgentData, CreateNewAgentVariables>;

interface GetMyAgentsRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetMyAgentsData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<GetMyAgentsData, undefined>;
  operationName: string;
}
export const getMyAgentsRef: GetMyAgentsRef;

export function getMyAgents(): QueryPromise<GetMyAgentsData, undefined>;
export function getMyAgents(dc: DataConnect): QueryPromise<GetMyAgentsData, undefined>;

interface UpdateAgentRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: UpdateAgentVariables): MutationRef<UpdateAgentData, UpdateAgentVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: UpdateAgentVariables): MutationRef<UpdateAgentData, UpdateAgentVariables>;
  operationName: string;
}
export const updateAgentRef: UpdateAgentRef;

export function updateAgent(vars: UpdateAgentVariables): MutationPromise<UpdateAgentData, UpdateAgentVariables>;
export function updateAgent(dc: DataConnect, vars: UpdateAgentVariables): MutationPromise<UpdateAgentData, UpdateAgentVariables>;

interface DeleteAgentRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: DeleteAgentVariables): MutationRef<DeleteAgentData, DeleteAgentVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: DeleteAgentVariables): MutationRef<DeleteAgentData, DeleteAgentVariables>;
  operationName: string;
}
export const deleteAgentRef: DeleteAgentRef;

export function deleteAgent(vars: DeleteAgentVariables): MutationPromise<DeleteAgentData, DeleteAgentVariables>;
export function deleteAgent(dc: DataConnect, vars: DeleteAgentVariables): MutationPromise<DeleteAgentData, DeleteAgentVariables>;

