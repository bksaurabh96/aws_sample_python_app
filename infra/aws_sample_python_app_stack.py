from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    CfnOutput,
)
from constructs import Construct


class AwsSamplePythonAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "AppVpc", max_azs=2)

        cluster = ecs.Cluster(self, "AppCluster", vpc=vpc)

        api_token = self.node.try_get_context("apiToken") or "changeme-token"

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "AppService",
            cluster=cluster,
            cpu=256,
            desired_count=1,
            memory_limit_mib=512,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    directory="..",
                ),
                container_port=8000,
                environment={
                    "API_TOKEN": api_token,
                },
            ),
        )

        # Use unauthenticated / endpoint for ALB health checks (required for target health)
        fargate_service.target_group.configure_health_check(
            path="/",
            healthy_http_codes="200",
        )

        CfnOutput(
            self,
            "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name,
            description="Public DNS name of the application load balancer",
        )

