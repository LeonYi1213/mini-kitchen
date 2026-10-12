require "base64"
require "json"
require "net/http"
require "openssl"
require "time"
require "uri"
API_ORIGIN = "https://api.appstoreconnect.apple.com"
def base64url(value)
  Base64.strict_encode64(value).tr("+/", "-_").delete("=")
end

class AppStoreConnectClient
  def initialize(key_id:, issuer_id:, private_key_path:, key_kind:)
    @key_id = key_id
    @issuer_id = issuer_id
    @key_kind = key_kind
    @private_key = OpenSSL::PKey.read(File.binread(private_key_path))
  end

  def get(path, query = {})
    uri = URI.join(API_ORIGIN, path)
    uri.query = URI.encode_www_form(query) unless query.empty?
    request(Net::HTTP::Get.new(uri), uri)
  end

  def post(path, body)
    uri = URI.join(API_ORIGIN, path)
    request(Net::HTTP::Post.new(uri), uri, body)
  end

  def patch(path, body)
    uri = URI.join(API_ORIGIN, path)
    request(Net::HTTP::Patch.new(uri), uri, body)
  end

  def all(path, query = {})
    records = []
    response = get(path, query)
    loop do
      records.concat(response.fetch("data"))
      next_url = response.dig("links", "next")
      break unless next_url

      uri = URI(next_url)
      response = request(Net::HTTP::Get.new(uri), uri)
    end
    records
  end

  private

  def request(request, uri, body = nil)
    request["Authorization"] = "Bearer #{token}"
    request["Content-Type"] = "application/json"
    request.body = JSON.generate(body) if body

    response = Net::HTTP.start(uri.host, uri.port, use_ssl: true, open_timeout: 15, read_timeout: 30) do |http|
      http.request(request)
    end

    parsed = response.body.to_s.empty? ? {} : JSON.parse(response.body)
    return parsed if response.code.to_i.between?(200, 299)

    details = Array(parsed["errors"]).map do |error|
      [error["status"], error["code"], error["title"], error["detail"]].compact.join(" ")
    end
    raise "App Store Connect returned HTTP #{response.code}: #{details.join(" | ")}"
  rescue JSON::ParserError
    raise "App Store Connect returned HTTP #{response.code} with a non-JSON response"
  end

  def token
    now = Time.now.to_i
    header = { alg: "ES256", kid: @key_id, typ: "JWT" }
    payload = { iat: now, exp: now + 600, aud: "appstoreconnect-v1" }
    if @key_kind == "individual"
      payload[:sub] = "user"
    else
      payload[:iss] = @issuer_id
    end

    signing_input = [
      base64url(JSON.generate(header)),
      base64url(JSON.generate(payload))
    ].join(".")
    der_signature = @private_key.sign(OpenSSL::Digest.new("SHA256"), signing_input)
    sequence = OpenSSL::ASN1.decode(der_signature)
    # ES256 JWTs carry two fixed-width unsigned integers, not ASCII binary digits.
    raw_signature = sequence.value.map { |integer| [integer.value.to_i.to_s(16).rjust(64, "0")].pack("H*") }.join
    "#{signing_input}.#{base64url(raw_signature)}"
  end
end
