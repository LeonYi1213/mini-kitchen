require_relative 'client'
account = JSON.parse(File.read('/Users/yeliyang/.codex/memories/app-delivery-connections.json')).fetch('apple_account')
config = JSON.parse(File.read(File.join(__dir__, 'release-config.json')))
client = AppStoreConnectClient.new(key_id: account.fetch('asc_key_id'), issuer_id: account.fetch('asc_issuer_id'), private_key_path: account.fetch('asc_private_key_path'), key_kind: 'team')
app_id = config.fetch('app_id')
abort 'App ID missing' unless app_id
app = client.get("/v1/apps/#{app_id}").fetch('data')
abort 'App identity mismatch' unless app.dig('attributes', 'bundleId') == config.fetch('bundle_id')
response = client.get('/v1/builds', 'filter[app]' => app_id, 'filter[version]' => config.fetch('build'), 'include' => 'buildBetaDetail')
build = response.fetch('data').first
unless build && build.dig('attributes','processingState') == 'VALID'
  puts JSON.generate({ready: false, state: build&.dig('attributes','processingState') || 'NOT_YET_VISIBLE'})
  exit 2
end
abort 'Build expired' if build.dig('attributes', 'expired')
build_id = build.fetch('id')
notes = File.read(File.join(__dir__, 'beta-notes.txt')).strip
localization = client.get("/v1/builds/#{build_id}/betaBuildLocalizations").fetch('data').find { |l| l.dig('attributes','locale') == 'zh-Hans' }
if localization
  client.patch("/v1/betaBuildLocalizations/#{localization.fetch('id')}", data: {type: 'betaBuildLocalizations', id: localization.fetch('id'), attributes: {whatsNew: notes}})
else
  client.post('/v1/betaBuildLocalizations', data: {type: 'betaBuildLocalizations', attributes: {locale: 'zh-Hans', whatsNew: notes}, relationships: {build: {data: {type: 'builds', id: build_id}}}})
end
group = client.get("/v1/apps/#{app_id}/betaGroups").fetch('data').find { |g| g.dig('attributes','name') == config.fetch('group_name') }
abort 'Private group missing' unless group && group.dig('attributes','isInternalGroup') && !group.dig('attributes','publicLinkEnabled')
group_id = group.fetch('id')
builds = client.get("/v1/betaGroups/#{group_id}/relationships/builds").fetch('data')
unless builds.any? { |b| b.fetch('id') == build_id }
  client.post("/v1/betaGroups/#{group_id}/relationships/builds", data: [{type: 'builds', id: build_id}])
end
# Only invite the existing account holder, not other contacts or project testers.
owners = client.get('/v1/users').fetch('data').select { |u| u.dig('attributes','roles').include?('ACCOUNT_HOLDER') }
abort 'Expected one account holder' unless owners.length == 1
owner_email = owners.first.dig('attributes','username')
testers = client.get("/v1/betaGroups/#{group_id}/betaTesters").fetch('data')
tester = testers.find { |t| t.dig('attributes','email') == owner_email }
abort 'Account holder not yet in private beta group' unless tester
if tester.dig('attributes','state') == 'NOT_INVITED'
  client.post('/v1/betaTesterInvitations', data: {type: 'betaTesterInvitations', relationships: {app: {data: {type: 'apps', id: app_id}}, betaTester: {data: {type: 'betaTesters', id: tester.fetch('id')}}}})
end
status = client.get("/v1/builds/#{build_id}/buildBetaDetail").fetch('data')
testers = client.get("/v1/betaGroups/#{group_id}/betaTesters").fetch('data')
puts JSON.pretty_generate({app_id: app_id, build_id: build_id, version: config.fetch('version'), build: config.fetch('build'), beta_state: status.fetch('attributes'), testers: testers.map { |t| {id: t['id'], state: t.dig('attributes','state')} }})
