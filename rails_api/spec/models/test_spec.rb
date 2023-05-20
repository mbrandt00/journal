require "rails_helper"

RSpec.describe "test" do
  it "will return a passing test" do
    expect(true).to be true
  end

  it "will return a failing test" do
    expect(true).to be false
  end
end
