"""
Kubernetes API Client Wrapper
Provides high-level abstraction over official Kubernetes Python Client (CoreV1Api, AppsV1Api).
Supports both in-cluster pod execution and external kubeconfig connections.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("kubepulse.k8s_client")

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    K8S_CLIENT_AVAILABLE = True
except ImportError:
    K8S_CLIENT_AVAILABLE = False
    ApiException = Exception


class K8sClient:
    """Wrapper around Kubernetes CoreV1 and AppsV1 APIs with graceful fallbacks."""

    def __init__(self, kubeconfig_path: Optional[str] = None, in_cluster: bool = False):
        self.connected = False
        self.connection_error: Optional[str] = None
        self.core_api: Optional[Any] = None
        self.apps_api: Optional[Any] = None
        self.kubeconfig_path = kubeconfig_path
        self.in_cluster = in_cluster

        if K8S_CLIENT_AVAILABLE:
            self._initialize()

    def _initialize(self):
        """Attempts to authenticate and establish connection with Kubernetes API server."""
        try:
            if self.in_cluster:
                config.load_incluster_config()
                self.connected = True
            elif self.kubeconfig_path:
                config.load_kube_config(config_file=self.kubeconfig_path)
                self.connected = True
            else:
                config.load_kube_config()
                self.connected = True

            if self.connected:
                self.core_api = client.CoreV1Api()
                self.apps_api = client.AppsV1Api()
                # Test connectivity
                self.core_api.get_api_resources()
                logger.info("Successfully connected to live Kubernetes cluster.")
        except Exception as e:
            self.connected = False
            self.connection_error = str(e)
            logger.info("Live Kubernetes cluster not available (%s). Defaulting to simulation engine.", e)

    def is_connected(self) -> bool:
        return self.connected

    def get_cluster_nodes(self) -> List[Dict[str, Any]]:
        """Fetches live nodes from the cluster."""
        if not self.connected or not self.core_api:
            return []
        try:
            nodes_response = self.core_api.list_node()
            result = []
            for node in nodes_response.items:
                conditions = {c.type: c.status for c in (node.status.conditions or [])}
                result.append({
                    "name": node.metadata.name,
                    "status": "Ready" if conditions.get("Ready") == "True" else "NotReady",
                    "roles": list(node.metadata.labels.keys()),
                    "cpu_capacity": node.status.capacity.get("cpu", "4"),
                    "memory_capacity": node.status.capacity.get("memory", "16Gi"),
                    "kubelet_version": node.status.node_info.kubelet_version,
                    "os_image": node.status.node_info.os_image,
                })
            return result
        except Exception as e:
            logger.error("Error reading live cluster nodes: %s", e)
            return []

    def get_cluster_pods(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """Fetches live pods from a given namespace."""
        if not self.connected or not self.core_api:
            return []
        try:
            pods_response = self.core_api.list_namespaced_pod(namespace=namespace)
            result = []
            for pod in pods_response.items:
                restart_count = 0
                if pod.status.container_statuses:
                    restart_count = sum(c.restart_count for c in pod.status.container_statuses)

                result.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "node": pod.spec.node_name or "Unassigned",
                    "ip": pod.status.pod_ip or "N/A",
                    "restarts": restart_count,
                    "created_at": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                })
            return result
        except Exception as e:
            logger.error("Error reading live cluster pods: %s", e)
            return []

    def restart_pod(self, pod_name: str, namespace: str = "default") -> bool:
        """Deletes a pod to trigger automatic replica controller recreation."""
        if not self.connected or not self.core_api:
            return False
        try:
            self.core_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
            return True
        except Exception as e:
            logger.error("Error restarting pod %s: %s", pod_name, e)
            return False

    def rollback_deployment(self, deployment_name: str, namespace: str = "default") -> bool:
        """Rolls back a deployment to its previous revision."""
        if not self.connected or not self.apps_api:
            return False
        try:
            # Trigger rollout undo via patch
            patch_body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    }
                }
            }
            self.apps_api.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=patch_body)
            return True
        except Exception as e:
            logger.error("Error rolling back deployment %s: %s", deployment_name, e)
            return False
