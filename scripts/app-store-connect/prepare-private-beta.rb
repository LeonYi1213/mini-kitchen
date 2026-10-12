require_relative 'client'
account = JSON.parse(File.read('/Users/yeliyang/.codex/memories/app-delivery-connections.json')).fetch('apple_account')
config_path = File.join(__dir__, 'release-config.json')
config = JSON.parse(File.read(config_path))
client = AppStoreConnectClient.new(key_id: account.fetch('asc_key_id'), issuer_id: account.fetch('asc_issuer_id'), private_key_path: account.fetch('asc_private_key_path'), key_kind: 'team')
apps = client.get('/v1/apps', 'filter[bundleId]' => config.fetch('bundle_id')).fetch('data')
abort 'MiniKitchen app record not yet created. Complete App Store Connect web setup first.' unless apps.length == 1
app = apps.first
app_id = app.fetch('id')
config['app_id'] = app_id
File.write(config_path, JSON.pretty_generate(config) + "\n")
groups = client.get("/v1/apps/#{app_id}/betaGroups").fetch('data')
group = groups.find { |g| g.dig('attributes', 'name') == config.fetch('group_name') }
unless group
  group = client.post('/v1/betaGroups', data: {type: 'betaGroups', attributes: {name: config.fetch('group_name'), isInternalGroup: true, publicLinkEnabled: false}, relationships: {app: {data: {type: 'apps', id: app_id}}}}).fetch('data')
end
abort 'Expected a private internal beta group' unless group.dig('attributes', 'isInternalGroup') && !group.dig('attributes', 'publicLinkEnabled')
localizations = client.get("/v1/apps/#{app_id}/betaAppLocalizations").fetch('data')
localization = localizations.find { |l| l.dig('attributes', 'locale') == 'zh-Hans' }
attributes = {description: File.read(File.join(__dir__, 'beta-notes.txt')).strip, feedbackEmail: 'app_liyang@163.com'}
if localization
  client.patch("/v1/betaAppLocalizations/#{localization.fetch('id')}", data: {type: 'betaAppLocalizations', id: localization.fetch('id'), attributes: attributes})
else
  client.post('/v1/betaAppLocalizations', data: {type: 'betaAppLocalizations', attributes: attributes.merge(locale: 'zh-Hans'), relationships: {app: {data: {type: 'apps', id: app_id}}}})
end
puts JSON.pretty_generate({app_id: app_id, group_id: group.fetch('id'), private_internal_group: true})
