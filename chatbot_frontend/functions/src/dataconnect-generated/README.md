# Generated TypeScript README
This README will guide you through the process of using the generated JavaScript SDK package for the connector `example`. It will also provide examples on how to use your generated SDK to call your Data Connect queries and mutations.

***NOTE:** This README is generated alongside the generated SDK. If you make changes to this file, they will be overwritten when the SDK is regenerated.*

# Table of Contents
- [**Overview**](#generated-javascript-readme)
- [**Accessing the connector**](#accessing-the-connector)
  - [*Connecting to the local Emulator*](#connecting-to-the-local-emulator)
- [**Queries**](#queries)
  - [*GetMyAgents*](#getmyagents)
- [**Mutations**](#mutations)
  - [*CreateNewAgent*](#createnewagent)
  - [*UpdateAgent*](#updateagent)
  - [*DeleteAgent*](#deleteagent)

# Accessing the connector
A connector is a collection of Queries and Mutations. One SDK is generated for each connector - this SDK is generated for the connector `example`. You can find more information about connectors in the [Data Connect documentation](https://firebase.google.com/docs/data-connect#how-does).

You can use this generated SDK by importing from the package `@dataconnect/generated` as shown below. Both CommonJS and ESM imports are supported.

You can also follow the instructions from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#set-client).

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig } from '@dataconnect/generated';

const dataConnect = getDataConnect(connectorConfig);
```

## Connecting to the local Emulator
By default, the connector will connect to the production service.

To connect to the emulator, you can use the following code.
You can also follow the emulator instructions from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#instrument-clients).

```typescript
import { connectDataConnectEmulator, getDataConnect } from 'firebase/data-connect';
import { connectorConfig } from '@dataconnect/generated';

const dataConnect = getDataConnect(connectorConfig);
connectDataConnectEmulator(dataConnect, 'localhost', 9399);
```

After it's initialized, you can call your Data Connect [queries](#queries) and [mutations](#mutations) from your generated SDK.

# Queries

There are two ways to execute a Data Connect Query using the generated Web SDK:
- Using a Query Reference function, which returns a `QueryRef`
  - The `QueryRef` can be used as an argument to `executeQuery()`, which will execute the Query and return a `QueryPromise`
- Using an action shortcut function, which returns a `QueryPromise`
  - Calling the action shortcut function will execute the Query and return a `QueryPromise`

The following is true for both the action shortcut function and the `QueryRef` function:
- The `QueryPromise` returned will resolve to the result of the Query once it has finished executing
- If the Query accepts arguments, both the action shortcut function and the `QueryRef` function accept a single argument: an object that contains all the required variables (and the optional variables) for the Query
- Both functions can be called with or without passing in a `DataConnect` instance as an argument. If no `DataConnect` argument is passed in, then the generated SDK will call `getDataConnect(connectorConfig)` behind the scenes for you.

Below are examples of how to use the `example` connector's generated functions to execute each query. You can also follow the examples from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#using-queries).

## GetMyAgents
You can execute the `GetMyAgents` query using the following action shortcut function, or by calling `executeQuery()` after calling the following `QueryRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
getMyAgents(): QueryPromise<GetMyAgentsData, undefined>;

interface GetMyAgentsRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetMyAgentsData, undefined>;
}
export const getMyAgentsRef: GetMyAgentsRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `QueryRef` function.
```typescript
getMyAgents(dc: DataConnect): QueryPromise<GetMyAgentsData, undefined>;

interface GetMyAgentsRef {
  ...
  (dc: DataConnect): QueryRef<GetMyAgentsData, undefined>;
}
export const getMyAgentsRef: GetMyAgentsRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the getMyAgentsRef:
```typescript
const name = getMyAgentsRef.operationName;
console.log(name);
```

### Variables
The `GetMyAgents` query has no variables.
### Return Type
Recall that executing the `GetMyAgents` query returns a `QueryPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `GetMyAgentsData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
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
```
### Using `GetMyAgents`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, getMyAgents } from '@dataconnect/generated';


// Call the `getMyAgents()` function to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await getMyAgents();

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await getMyAgents(dataConnect);

console.log(data.agents);

// Or, you can use the `Promise` API.
getMyAgents().then((response) => {
  const data = response.data;
  console.log(data.agents);
});
```

### Using `GetMyAgents`'s `QueryRef` function

```typescript
import { getDataConnect, executeQuery } from 'firebase/data-connect';
import { connectorConfig, getMyAgentsRef } from '@dataconnect/generated';


// Call the `getMyAgentsRef()` function to get a reference to the query.
const ref = getMyAgentsRef();

// You can also pass in a `DataConnect` instance to the `QueryRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = getMyAgentsRef(dataConnect);

// Call `executeQuery()` on the reference to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeQuery(ref);

console.log(data.agents);

// Or, you can use the `Promise` API.
executeQuery(ref).then((response) => {
  const data = response.data;
  console.log(data.agents);
});
```

# Mutations

There are two ways to execute a Data Connect Mutation using the generated Web SDK:
- Using a Mutation Reference function, which returns a `MutationRef`
  - The `MutationRef` can be used as an argument to `executeMutation()`, which will execute the Mutation and return a `MutationPromise`
- Using an action shortcut function, which returns a `MutationPromise`
  - Calling the action shortcut function will execute the Mutation and return a `MutationPromise`

The following is true for both the action shortcut function and the `MutationRef` function:
- The `MutationPromise` returned will resolve to the result of the Mutation once it has finished executing
- If the Mutation accepts arguments, both the action shortcut function and the `MutationRef` function accept a single argument: an object that contains all the required variables (and the optional variables) for the Mutation
- Both functions can be called with or without passing in a `DataConnect` instance as an argument. If no `DataConnect` argument is passed in, then the generated SDK will call `getDataConnect(connectorConfig)` behind the scenes for you.

Below are examples of how to use the `example` connector's generated functions to execute each mutation. You can also follow the examples from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#using-mutations).

## CreateNewAgent
You can execute the `CreateNewAgent` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
createNewAgent(vars: CreateNewAgentVariables): MutationPromise<CreateNewAgentData, CreateNewAgentVariables>;

interface CreateNewAgentRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateNewAgentVariables): MutationRef<CreateNewAgentData, CreateNewAgentVariables>;
}
export const createNewAgentRef: CreateNewAgentRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
createNewAgent(dc: DataConnect, vars: CreateNewAgentVariables): MutationPromise<CreateNewAgentData, CreateNewAgentVariables>;

interface CreateNewAgentRef {
  ...
  (dc: DataConnect, vars: CreateNewAgentVariables): MutationRef<CreateNewAgentData, CreateNewAgentVariables>;
}
export const createNewAgentRef: CreateNewAgentRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the createNewAgentRef:
```typescript
const name = createNewAgentRef.operationName;
console.log(name);
```

### Variables
The `CreateNewAgent` mutation requires an argument of type `CreateNewAgentVariables`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface CreateNewAgentVariables {
  name: string;
  personality: string;
  knowledgeBase?: string | null;
  purpose?: string | null;
  isPublic?: boolean | null;
}
```
### Return Type
Recall that executing the `CreateNewAgent` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `CreateNewAgentData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface CreateNewAgentData {
  agent_insert: Agent_Key;
}
```
### Using `CreateNewAgent`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, createNewAgent, CreateNewAgentVariables } from '@dataconnect/generated';

// The `CreateNewAgent` mutation requires an argument of type `CreateNewAgentVariables`:
const createNewAgentVars: CreateNewAgentVariables = {
  name: ..., 
  personality: ..., 
  knowledgeBase: ..., // optional
  purpose: ..., // optional
  isPublic: ..., // optional
};

// Call the `createNewAgent()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await createNewAgent(createNewAgentVars);
// Variables can be defined inline as well.
const { data } = await createNewAgent({ name: ..., personality: ..., knowledgeBase: ..., purpose: ..., isPublic: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await createNewAgent(dataConnect, createNewAgentVars);

console.log(data.agent_insert);

// Or, you can use the `Promise` API.
createNewAgent(createNewAgentVars).then((response) => {
  const data = response.data;
  console.log(data.agent_insert);
});
```

### Using `CreateNewAgent`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, createNewAgentRef, CreateNewAgentVariables } from '@dataconnect/generated';

// The `CreateNewAgent` mutation requires an argument of type `CreateNewAgentVariables`:
const createNewAgentVars: CreateNewAgentVariables = {
  name: ..., 
  personality: ..., 
  knowledgeBase: ..., // optional
  purpose: ..., // optional
  isPublic: ..., // optional
};

// Call the `createNewAgentRef()` function to get a reference to the mutation.
const ref = createNewAgentRef(createNewAgentVars);
// Variables can be defined inline as well.
const ref = createNewAgentRef({ name: ..., personality: ..., knowledgeBase: ..., purpose: ..., isPublic: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = createNewAgentRef(dataConnect, createNewAgentVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.agent_insert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.agent_insert);
});
```

## UpdateAgent
You can execute the `UpdateAgent` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
updateAgent(vars: UpdateAgentVariables): MutationPromise<UpdateAgentData, UpdateAgentVariables>;

interface UpdateAgentRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: UpdateAgentVariables): MutationRef<UpdateAgentData, UpdateAgentVariables>;
}
export const updateAgentRef: UpdateAgentRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
updateAgent(dc: DataConnect, vars: UpdateAgentVariables): MutationPromise<UpdateAgentData, UpdateAgentVariables>;

interface UpdateAgentRef {
  ...
  (dc: DataConnect, vars: UpdateAgentVariables): MutationRef<UpdateAgentData, UpdateAgentVariables>;
}
export const updateAgentRef: UpdateAgentRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the updateAgentRef:
```typescript
const name = updateAgentRef.operationName;
console.log(name);
```

### Variables
The `UpdateAgent` mutation requires an argument of type `UpdateAgentVariables`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface UpdateAgentVariables {
  id: UUIDString;
  name?: string | null;
  personality?: string | null;
  knowledgeBase?: string | null;
  purpose?: string | null;
  isPublic?: boolean | null;
}
```
### Return Type
Recall that executing the `UpdateAgent` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `UpdateAgentData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface UpdateAgentData {
  agent_update?: Agent_Key | null;
}
```
### Using `UpdateAgent`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, updateAgent, UpdateAgentVariables } from '@dataconnect/generated';

// The `UpdateAgent` mutation requires an argument of type `UpdateAgentVariables`:
const updateAgentVars: UpdateAgentVariables = {
  id: ..., 
  name: ..., // optional
  personality: ..., // optional
  knowledgeBase: ..., // optional
  purpose: ..., // optional
  isPublic: ..., // optional
};

// Call the `updateAgent()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await updateAgent(updateAgentVars);
// Variables can be defined inline as well.
const { data } = await updateAgent({ id: ..., name: ..., personality: ..., knowledgeBase: ..., purpose: ..., isPublic: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await updateAgent(dataConnect, updateAgentVars);

console.log(data.agent_update);

// Or, you can use the `Promise` API.
updateAgent(updateAgentVars).then((response) => {
  const data = response.data;
  console.log(data.agent_update);
});
```

### Using `UpdateAgent`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, updateAgentRef, UpdateAgentVariables } from '@dataconnect/generated';

// The `UpdateAgent` mutation requires an argument of type `UpdateAgentVariables`:
const updateAgentVars: UpdateAgentVariables = {
  id: ..., 
  name: ..., // optional
  personality: ..., // optional
  knowledgeBase: ..., // optional
  purpose: ..., // optional
  isPublic: ..., // optional
};

// Call the `updateAgentRef()` function to get a reference to the mutation.
const ref = updateAgentRef(updateAgentVars);
// Variables can be defined inline as well.
const ref = updateAgentRef({ id: ..., name: ..., personality: ..., knowledgeBase: ..., purpose: ..., isPublic: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = updateAgentRef(dataConnect, updateAgentVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.agent_update);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.agent_update);
});
```

## DeleteAgent
You can execute the `DeleteAgent` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
deleteAgent(vars: DeleteAgentVariables): MutationPromise<DeleteAgentData, DeleteAgentVariables>;

interface DeleteAgentRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: DeleteAgentVariables): MutationRef<DeleteAgentData, DeleteAgentVariables>;
}
export const deleteAgentRef: DeleteAgentRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
deleteAgent(dc: DataConnect, vars: DeleteAgentVariables): MutationPromise<DeleteAgentData, DeleteAgentVariables>;

interface DeleteAgentRef {
  ...
  (dc: DataConnect, vars: DeleteAgentVariables): MutationRef<DeleteAgentData, DeleteAgentVariables>;
}
export const deleteAgentRef: DeleteAgentRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the deleteAgentRef:
```typescript
const name = deleteAgentRef.operationName;
console.log(name);
```

### Variables
The `DeleteAgent` mutation requires an argument of type `DeleteAgentVariables`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface DeleteAgentVariables {
  id: UUIDString;
}
```
### Return Type
Recall that executing the `DeleteAgent` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `DeleteAgentData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface DeleteAgentData {
  agent_delete?: Agent_Key | null;
}
```
### Using `DeleteAgent`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, deleteAgent, DeleteAgentVariables } from '@dataconnect/generated';

// The `DeleteAgent` mutation requires an argument of type `DeleteAgentVariables`:
const deleteAgentVars: DeleteAgentVariables = {
  id: ..., 
};

// Call the `deleteAgent()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await deleteAgent(deleteAgentVars);
// Variables can be defined inline as well.
const { data } = await deleteAgent({ id: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await deleteAgent(dataConnect, deleteAgentVars);

console.log(data.agent_delete);

// Or, you can use the `Promise` API.
deleteAgent(deleteAgentVars).then((response) => {
  const data = response.data;
  console.log(data.agent_delete);
});
```

### Using `DeleteAgent`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, deleteAgentRef, DeleteAgentVariables } from '@dataconnect/generated';

// The `DeleteAgent` mutation requires an argument of type `DeleteAgentVariables`:
const deleteAgentVars: DeleteAgentVariables = {
  id: ..., 
};

// Call the `deleteAgentRef()` function to get a reference to the mutation.
const ref = deleteAgentRef(deleteAgentVars);
// Variables can be defined inline as well.
const ref = deleteAgentRef({ id: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = deleteAgentRef(dataConnect, deleteAgentVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.agent_delete);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.agent_delete);
});
```

