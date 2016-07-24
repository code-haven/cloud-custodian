from c7n.utils import query_instances
from common import BaseTest, event_data


class AutoTagCreator(BaseTest):

    def test_auto_tag_assumed(self):
        # verify auto tag works with assumed roles and can optionally update
        session_factory = self.replay_flight_data('test_ec2_autotag_assumed')
        policy = self.load_policy({
            'name': 'ec2-auto-tag',
            'resource': 'ec2',
            'mode': {
                'type': 'cloudtrail',
                'events': ['RunInstances']},
            'actions': [
                {'type': 'auto-tag-user',
                 'update': True,
                 'tag': 'Owner'}]
        }, session_factory=session_factory)

        event = {
            'detail': event_data(
                'event-cloud-trail-run-instance-creator-assumed.json'),
            'debug': True}
        resources = policy.push(event, None)
        self.assertEqual(len(resources), 1)
        tags = {t['Key']: t['Value'] for t in resources[0]['Tags']}
        self.assertEqual(tags['Owner'], 'Bob')

        session = session_factory()
        instances = query_instances(
            session, InstanceIds=[resources[0]['InstanceId']])
        tags = {t['Key']: t['Value'] for t in instances[0]['Tags']}
        self.assertEqual(tags['Owner'], 'Radiant')

    def test_auto_tag_creator(self):
        session_factory = self.replay_flight_data('test_ec2_autotag_creator')
        policy = self.load_policy({
            'name': 'ec2-auto-tag',
            'resource': 'ec2',
            'mode': {
                'type': 'cloudtrail',
                'events': ['RunInstances']},
            'actions': [
                {'type': 'auto-tag-user',
                 'tag': 'Owner'}]
        }, session_factory=session_factory)

        event = {
            'detail': event_data('event-cloud-trail-run-instance-creator.json'),
            'debug': True}
        resources = policy.push(event, None)
        self.assertEqual(len(resources), 1)

        # Verify tag added
        session = session_factory()
        instances = query_instances(
            session, InstanceIds=[resources[0]['InstanceId']])
        tags = {t['Key']: t['Value'] for t in instances[0]['Tags']}
        self.assertEqual(tags['Owner'], 'c7nbot')

        # Verify we don't overwrite extant
        client = session.client('ec2')
        client.create_tags(
            Resources=[resources[0]['InstanceId']],
            Tags=[{'Key': 'Owner', 'Value': 'Bob'}])

        policy = self.load_policy({
            'name': 'ec2-auto-tag',
            'resource': 'ec2',
            'mode': {
                'type': 'cloudtrail',
                'events': ['RunInstances']},
            'actions': [
                {'type': 'auto-tag-user',
                 'tag': 'Owner'}]
        }, session_factory=session_factory)

        resources = policy.push(event, None)
        instances = query_instances(
            session, InstanceIds=[resources[0]['InstanceId']])
        tags = {t['Key']: t['Value'] for t in instances[0]['Tags']}
        self.assertEqual(tags['Owner'], 'Bob')
