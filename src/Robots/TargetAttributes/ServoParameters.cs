namespace Robots;

/// <summary>
/// Parameters for servoj motion command (UR robots only).
/// Enables low-level position control with per-point timing for dense trajectories.
/// </summary>
public class ServoParameters(double timeStep = 0.008, double lookaheadTime = 0.1, double gain = 300, string? name = null)
    : TargetAttribute(name), IEquatable<ServoParameters>
{
    public static ServoParameters Default { get; } = new(name: "DefaultServo");

    /// <summary>
    /// Time step in seconds. Use 0.008 for CB3 (125Hz) or 0.002 for e-Series (500Hz).
    /// </summary>
    public double TimeStep { get; set; } = timeStep;

    /// <summary>
    /// Lookahead time in seconds (0.03-0.2). Controls trajectory smoothing.
    /// Lower values give faster response but may cause vibrations.
    /// </summary>
    public double LookaheadTime { get; set; } = lookaheadTime;

    /// <summary>
    /// Proportional gain (100-2000). Higher values give faster position tracking.
    /// High gain with noisy or sparse targets may cause instability.
    /// </summary>
    public double Gain { get; set; } = gain;

    public override int GetHashCode() => TimeStep.GetHashCode() ^ LookaheadTime.GetHashCode() ^ Gain.GetHashCode();
    public override bool Equals(object? obj) => obj is ServoParameters other && Equals(other);

    public bool Equals(ServoParameters? other)
    {
        if (other is null) return false;
        return TimeStep == other.TimeStep
            && LookaheadTime == other.LookaheadTime
            && Gain == other.Gain
            && _name == other._name;
    }

    public override string ToString() => HasName
        ? $"Servo ({Name})"
        : $"Servo (t={TimeStep:0.###}s, lookahead={LookaheadTime:0.##}, gain={Gain:0})";
}
