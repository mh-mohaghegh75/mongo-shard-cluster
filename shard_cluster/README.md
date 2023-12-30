This blog is going to demonstrate the setup of Sharded MongoDB Cluster on Google Kubernetes Engine. We will use kubernetes StatefulSets feature to deploy mongodb containers.

We need to cover some concepts before we move on to demonstration.

StatefulSets
A StatefulSets is like a Deployment which manages Pods and guarantees about the ordering and uniqueness of these Pods. It maintains a sticky identity for each of their Pods. It helps in deployment of application that needs persistency, unique network identifiers (DNS, Hostnames etc) and are meants for stateful application. If a pod gets terminated or deleted, a volume data will remain intact if managed by persistentvolumes.

StorageClass
StorageClass helps in administration to describe the “classes” of storage offered by Kubernetes. Each StorageClass has different provisioner (GCEPersistentDisk, AWSElasticBlockStore, AzureDisk etc) that determines what volume plugin is used for provisioning storage.

PersistentVolume
A PersistentVolume (PV) is a piece of storage in the cluster that has been provisioned by an administrator. PVs are resources available to be used by any Pod. Any Pod can claim these volumes by mean of PersistentVolumeClaims (PVC) and released eventually when claim is deleted.

Headless Services
Headless Services are used to configure DNS of pods having same selectors defined by services. It is not generally used for load-balancing purpose. Each headless services configured with label selectors helps in defining unique network identifiers for pods running in statefulset.

Lets begins the demonstration. Please switch to your terminal and follow the instructions.

Note : This setup is compatible with <= mongo 3.2.

1. Prerequisites
Ensure the following dependencies are already fulfilled on your host Linux system:

GCP’s cloud client command line tool gcloud
gcloud authentication to a project to manage container engine.
Install the Kubernetes command tool (“kubectl”),
Configure kubernetes authentication credentials.
2. Create namespace, storageclass, Google compute Disk and persistentvolumes.
Our Mongodb Setup will be as follows :

1x Config Server (k8s deployment type: “StatefulSet”)
2x Shards with each Shard being a Replica Set containing 1x replicas (k8s deployment type: “StatefulSet”)
2x Mongos Routers (k8s deployment type: “Deployment”)
We will create a kubernetes namespace and will deploy all our above resources in our defined namespaces. We will define disk that will be used by our statefulset containers. Disk will be mounted on pods running our mongodb server by means of APIs defined in StorageClass and PersistentVolume.


3. StatefulSet containers and Mongos Deployment.
3.1 Statefulset ConfigDB
Create a file as mongodb-configdb-service-stateful.yaml and copy the following template. Replace NAMESPACE_ID with daemonsl, or whatever name you have defined and DB_DISK with 5Gi.

We have created a headless service with clusterIP None with selector as role: mongodb-configdb listening to port 27019. We have defined our statefulset definition with mongodb arguments and volumeClaimTemplates. Here, VolumeClaimTemplates is requesting storageclass fast with storage capacity 5GB. This volumeClaimTemplates register this requests to storageclass and storageclass fulfill this requests by PersistentVolume (PV) and register claim in PersistentVolumeClaims (PVC).

apiVersion: v1
kind: Service
metadata:
  name: mongodb-configdb-headless-service
  labels:
    name: mongodb-configdb
spec:
  ports:
  - port: 27019
    targetPort: 27019
  clusterIP: None
  selector:
    role: mongodb-configdb
---
apiVersion: apps/v1 
kind: StatefulSet
metadata:
  name: mongodb-configdb
spec:
  selector:
    matchLabels:
      role: mongodb-configdb # has to match .spec.template.metadata.labels
  serviceName: mongodb-configdb-headless-service
  replicas: 2
  template:
    metadata:
      labels:
        role: mongodb-configdb
        tier: configdb
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: tier
                  operator: In
                  values:
                  - configdb
              topologyKey: kubernetes.io/hostname
      terminationGracePeriodSeconds: 10
      containers:
        - name: mongodb-configdb-container
          image: mongo:5.0.23
          command: ["/bin/sh"]
          args: ["-c", "mongod --port 27019 --bind_ip 0.0.0.0 --configsvr --replSet=Config"]
          resources:
            requests:
              cpu: 50m
              memory: 100Mi
          ports:
            - containerPort: 27019
  

Now, apply resources via kubectl~

$ kubectl apply -f mongodb-configdb-service-stateful.yaml

3.2 Statefulset mainDB
Create a file as mongodb-maindb-service-stateful.yaml and copy the following template. Replace NAMESPACE_ID with daemonsl, or whatever name you have defined, DB_DISK with 10Giand shardX & ShardX to 1 and then 2 and apply template two times to create two different statefulsets configuration. After deploying in kubernetes, we will have two statefulsets running with name as mongodb-shard1 and mongodb-shard2

Here again, We have created headless service and VolumeClaimTemplates which is requesting storageclass fast with storage capacity 10GB.

#tmp-mongodb-maindb-service-stateful1.yaml
apiVersion: v1
kind: Service
metadata:
  name: mongodb-shard1-headless-service
  labels:
    name: mongodb-shard1
spec:
  ports:
  - port: 27017
    targetPort: 27017
  clusterIP: None
  selector:
    role: mongodb-shard1
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb-shard1
spec:
  selector:
    matchLabels:
      role: mongodb-shard1 # has to match .spec.template.metadata.labels
  serviceName: mongodb-shard1-headless-service
  replicas: 2
  template:
    metadata:
      labels:
        role: mongodb-shard1
        tier: maindb
        replicaset: Shard1
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: replicaset
                  operator: In
                  values:
                  - Shard1
              topologyKey: kubernetes.io/hostname
      terminationGracePeriodSeconds: 10
      containers:
        - name: mongodb-shard1-container
          image: mongo:5.0.23
          command: ["/bin/sh"]
          args: ["-c", "mongod --shardsvr --replSet=Shard1 --bind_ip_all "]
          resources:
            requests:
              cpu: 50m
              memory: 100Mi
          ports:
            - containerPort: 27017

#tmp-mongodb-maindb-service-stateful2.yaml
apiVersion: v1
kind: Service
metadata:
  name: mongodb-shard2-headless-service
  labels:
    name: mongodb-shard2
spec:
  ports:
  - port: 27017
    targetPort: 27017
  clusterIP: None
  selector:
    role: mongodb-shard2
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb-shard2
spec:
  selector:
    matchLabels:
      role: mongodb-shard2 # has to match .spec.template.metadata.labels
  serviceName: mongodb-shard2-headless-service
  replicas: 2
  template:
    metadata:
      labels:
        role: mongodb-shard2
        tier: maindb
        replicaset: Shard2
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: replicaset
                  operator: In
                  values:
                  - Shard2
              topologyKey: kubernetes.io/hostname
      terminationGracePeriodSeconds: 10
      containers:
        - name: mongodb-shard2-container
          image: mongo:5.0.23
          command: ["/bin/sh"]
          args: ["-c", "mongod --shardsvr --replSet=Shard2 --bind_ip_all "]
          resources:
            requests:
              cpu: 50m
              memory: 100Mi
          ports:
            - containerPort: 27017

Apply resources via kubectl~


$ kubectl apply -f tmp-mongodb-maindb-service-stateful1.yaml

$ kubectl apply -f tmp-mongodb-maindb-service-stateful2.yaml
#run command to see Pods & Services spinning up
$ kubectl get svc,po --namespace=daemonsl
Till here, we have accomplished statefulsets container running along with headless services and mounted a SSD volume that fulfills Pods requirement.


3.3 Mongos Deployment
We have configdb and maindb pods up and running. We will spin up mongos server to establish a sharding cluster. Replace NAMESPACE_ID with daemonsl, or whatever name you have defined.

We have configured config server information in mongos using --configdb flag with unique network identifiers of configdb pod. DNS of statefulset pods goes by convention <POD_NAME>.<SERVICE_NAME>.<NAMESPACE>.svc.<CLUSTER_DOMAIN>.

Reference : https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#stable-network-id

apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongos
spec:
  selector:
    matchLabels:
      role: mongos
  replicas: 2
  template:
    metadata:
      labels:
        role: mongos
        tier: routers
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: tier
                  operator: In
                  values:
                  - routers
              topologyKey: kubernetes.io/hostname
      terminationGracePeriodSeconds: 10
      containers:
        - name: mongos-container
          image: mongo:5.0.23
          command: ["/bin/sh"]
          args: ["-c", "mongos --port 27017 --bind_ip_all --configdb Config/mongodb-configdb-0.mongodb-configdb-headless-service.default.svc.cluster.local:27019"]
          resources:
            # requests:
            #   cpu: 50m
            #   memory: 100Mi
          ports:
            - containerPort: 27017

Apply resources via kubectl~


$ kubectl apply -f tmp-mongodb-mongos-deployment-service.yaml

4. Configuring servers
Now, we have mongos, configdb and maindb up and running. We need to create Replicaset in MainDB servers that we are intending to make shard. We will run rs.initiate() command to make PRIMARY replica. Since we are going with one replica member in each shard. We will run initiate command in each of the maindb pod.


4.1. Configuring config server replica set 
Connect to one of the config servers.
Connect mongosh to one of the config server members.

$ kubectl exec -it mongodb-configdb-0 -- mongosh --port 27019 --eval "rs.initiate({_id: \"Config\", configsvr: true, members: [ {_id: 0, host: \"mongodb-configdb-0.mongodb-configdb-headless-service.default.svc.cluster.local:27019\"}, {_id: 1, host:\"mongodb-configdb-1.mongodb-configdb-headless-service.default.svc.cluster.local:27019\"} ] });"


4.1. Configuring shard server replica set 

echo "Replicaset Init mongodb-shard1-0 "

$ kubectl exec -it mongodb-shard1-0 -- mongosh --port 27018 --eval "rs.initiate({_id: \"Shard1\", members: [ {_id: 0, host: \"mongodb-shard1-0.mongodb-shard1-headless-service.default.svc.cluster.local:27018\"}, {_id: 1, host:\"mongodb-shard1-1.mongodb-shard1-headless-service.default.svc.cluster.local:27018\"} ] });"

echo "Replicaset Init mongodb-shard2-0 "  

$ kubectl exec -it mongodb-shard2-0 -- mongosh --port 27018 --eval "rs.initiate({_id: \"Shard2\", members: [ {_id: 0, host: \"mongodb-shard2-0.mongodb-shard2-headless-service.default.svc.cluster.local:27018\"}, {_id: 1, host:\"mongodb-shard2-1.mongodb-shard2-headless-service.default.svc.cluster.local:27018\"} ] });"

4.3. Start a mongos for the Sharded Cluster
If using command line parameters start the mongos and specify the --configdb, --bind_ip, and other options as appropriate to your deployment. For example:

# Shard1 mongos config  
echo "Adding Shard 1 : Shard1 "

$ kubectl exec -it $(kubectl get pod -l "tier=routers" -o jsonpath='{.items[0].metadata.name}' ) -- mongosh --port 27017 --eval "sh.addShard( \"Shard1/mongodb-shard1-0.mongodb-shard1-headless-service.default.svc.cluster.local:27018,mongodb-shard1-1.mongodb-shard1-headless-service.default.svc.cluster.local:27018\")"

# Shard2 mongos config
echo "Adding Shard 2 : Shard2 "

$ kubectl exec -it $(kubectl get pod -l "tier=routers" -o jsonpath='{.items[1].metadata.name}' ) -- mongosh --port 27017 --eval "sh.addShard( \"Shard2/mongodb-shard2-0.mongodb-shard2-headless-service.default.svc.cluster.local:27018,mongodb-shard2-1.mongodb-shard2-headless-service.default.svc.cluster.local:27018\")"

Above lines, will make both pods PRIMARY of their respective replicaset. You can even go into container to verify replicaset status by running rs.status() command.

We are proceeding now to add shards to mongos server. We will run below command in any of the mongos pod. Mongos server are stateless application, they save the configuration in configdb server which we have made stateful application by declaring them under statefulset container.



Now, we can get into one of the mongos container to verify the sharding status of cluster. All the above steps can be automated to make any number of shards within your cluster and thus concepts are very trivial to support stateful application powered by GKE.

Test Sharding
To test that the sharded cluster is working properly, connect to the container running the first “mongos” router, then use the Mongo Shell to authenticate, enable sharding on a specific database & collection, add some test data to this collection and then view the status of the Sharded cluster and collection:

$ kubectl exec -it $(kubectl get pod -l "tier=routers" -o jsonpath='{.items[0].metadata.name}') bash
$ mongo
> sh.enableSharding("<Database_name>");
> sh.status();
> use admin
> db.admin.runCommand("getShardMap")
